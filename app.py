import streamlit as st
import pandas as pd
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine
import urllib
import re
from dotenv import load_dotenv
import traceback

import os
from openai import AzureOpenAI

# 🌎 환경 변수 로드
load_dotenv()

# 🗂️ Azure Blob Storage 연결
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))

# 🛢️ Azure SQL 연결
server = os.getenv("AZURE_SQL_SERVER")
database = os.getenv("AZURE_SQL_DATABASE")
username = os.getenv("AZURE_SQL_USERNAME")
password = os.getenv("AZURE_SQL_PASSWORD")

def reset_session():
    for key in st.session_state.keys():
        del st.session_state[key]

def reset_session_and_delete_blobs():
    try:
        container_client = blob_service_client.get_container_client("report-data")
        for filename in st.session_state.get("uploaded_filenames", []):
            blob_client = container_client.get_blob_client(filename)
            blob_client.delete_blob()
        st.success("🧹 업로드된 파일도 모두 삭제되었습니다.")
    except Exception as e:
        st.warning(f"⚠️ 파일 삭제 중 오류 발생: {e}")

    # 세션 상태 초기화
    st.session_state.clear()
    st.rerun()

try:
    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    #st.success("✅ SQL 연결 성공!")
except Exception as e:
    st.error(f"❌ SQL 연결 실패: {e}")

# 🤖 Azure OpenAI 설정
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_endpoint = os.getenv("OPENAI_API_ENDPOINT")
openai_api_version = os.getenv("OPENAI_API_VERSION")

gpt_client = AzureOpenAI(
    api_version=openai_api_version,
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
)

# 📊 Streamlit UI
st.title("📊 보고서 작성")

if st.button("🔄 초기화"):
    reset_session()
    reset_session_and_delete_blobs()
    st.session_state["file_uploader"] = None
    st.session_state["uploaded_filenames"] = []  # 업로드된 파일 목록 초기화

uploaded_files = st.file_uploader("CSV 파일 업로드", type="csv", accept_multiple_files=True, key="file_uploader")

dataframes = {}

if uploaded_files:
    container_name = "report-data"
    try:
        container_client = blob_service_client.get_container_client(container_name)
        container_client.create_container()
    except Exception:
        pass

    st.subheader("📁 업로드된 파일 목록 및 미리보기")
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(uploaded_file, encoding='cp949')
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding='euc-kr')
        
        table_name = uploaded_file.name.replace(".csv", "").replace(" ", "_")
        dataframes[table_name] = df

        try:
            blob_client = container_client.get_blob_client(uploaded_file.name)
            blob_client.upload_blob(uploaded_file.getvalue(), overwrite=True)
            st.success(f"✅ '{uploaded_file.name}' 업로드 완료")
        except Exception as e:
            st.error(f"❌ Blob Storage 업로드 실패: {e}")

        try:
            from sqlalchemy.types import NVARCHAR

            # 문자열 컬럼에 대해 NVARCHAR 지정
            sql_types = {col: NVARCHAR(length=255) for col in df.columns if df[col].dtype == 'object'}

            df.to_sql(table_name, engine, if_exists='replace', index=False, dtype=sql_types)
            st.success(f"🗃️ Azure SQL에 테이블 '{table_name}' 저장 완료")
        except Exception as e:
            st.error(f"❌ SQL 업로드 실패: {e}")

        st.dataframe(df)

    st.subheader("🧠 자연어 입력")
    user_prompt = st.text_area("어떤 자료를 원하세요?", key="report_prompt")

    if st.button("자료 추출") and user_prompt:
        table_info = "\n".join([f"{name}:\n{df.head(3).to_csv(index=False)}" for name, df in dataframes.items()])
        full_prompt = f"""
다음은 컨테이너에서 읽은 CSV 파일 데이터입니다. 사용자의 요청에 따라 데이터를 조회하는 SQL 쿼리를 생성하세요.
테이블 목록:
{table_info}

사용자 요청:
{user_prompt}

SQL 쿼리:"""

        try:
            response = gpt_client.chat.completions.create(
                model="user09-dev-gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert SQL data analyst. Use only the columns and tables provided. Do not assume any additional fields. Generate only the SQL query."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=500,
                temperature=0
            )

            sql_query = response.choices[0].message.content.strip()

            # ✅ 백틱 제거 및 sql 접두어 제거
            sql_query = sql_query.replace("`", "")
            sql_query = re.sub(r'^\s*sql\s+', '', sql_query, flags=re.IGNORECASE).strip()

            st.code(sql_query, language="sql")

            with engine.connect() as conn:
                result_df = pd.read_sql_query(sql_query, conn)

                # 한글이 깨져서 byte로 들어왔을 경우 utf-8로 decode 시도
                def try_decode(val):
                    if isinstance(val, bytes):
                        try:
                            return val.decode('utf-8')
                        except:
                            return val
                    return val

                result_df = result_df.applymap(try_decode)

                st.success("✅ 데이터 조회 성공!")
                print(result_df.head())
                st.dataframe(result_df)
                st.download_button("📥 결과 CSV 다운로드", result_df.to_csv(index=False, encoding='utf-8-sig'), "query_result.csv", "text/csv")
        except Exception as e:
            st.error(f"❌ GPT 호출 오류: {e}")
            st.text(traceback.format_exc())