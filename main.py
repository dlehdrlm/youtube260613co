```python
import streamlit as st
import pandas as pd
import re
import os
import urllib.request
from collections import Counter

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    layout="wide"
)

st.title("🎬 유튜브 댓글 심층 분석기")

api_key = st.text_input(
    "YouTube API Key",
    type="password"
)

youtube_url = st.text_input(
    "유튜브 링크 입력"
)


def get_video_id(url):
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)"
    ]

    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)

    return None


def get_comments(video_id, api_key):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:

        try:
            response = request.execute()

        except HttpError as e:
            st.error(f"YouTube API 오류: {e}")
            st.stop()

        for item in response["items"]:

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "author": snippet["authorDisplayName"],
                "comment": snippet["textDisplay"],
                "likes": snippet["likeCount"]
            })

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return pd.DataFrame(comments)


def clean_text(text):

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^가-힣a-zA-Z\s]", " ", text)

    return text


if st.button("분석 시작"):

    if not api_key:
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = get_video_id(youtube_url)

    if not video_id:
        st.error("유효한 유튜브 링크가 아닙니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):

        df = get_comments(video_id, api_key)

    if len(df) == 0:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"{len(df):,}개 댓글 수집 완료")

    st.subheader("📊 기본 통계")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "댓글 수",
        len(df)
    )

    col2.metric(
        "평균 댓글 길이",
        round(df["comment"].str.len().mean(), 1)
    )

    col3.metric(
        "총 좋아요",
        int(df["likes"].sum())
    )

    st.subheader("🔥 인기 댓글 TOP 10")

    st.dataframe(
        df.sort_values(
            "likes",
            ascending=False
        ).head(10),
        use_container_width=True
    )

    text = " ".join(
        df["comment"].astype(str)
    )

    cleaned = clean_text(text)

    words = cleaned.split()

    stopwords = {
        "그리고",
        "그냥",
        "진짜",
        "너무",
        "정말",
        "이거",
        "저거",
        "영상",
        "있다",
        "같다",
        "하는",
        "에서",
        "으로",
        "입니다",
        "ㅋㅋ",
        "ㅎㅎ",
        "하면",
        "하면은",
        "있는",
        "있는데",
        "있는듯",
        "하는데"
    }

    words = [
        w for w in words
        if len(w) > 1
        and w not in stopwords
    ]

    counter = Counter(words)

    st.subheader("📈 단어 빈도 TOP 20")

    freq_df = pd.DataFrame(
        counter.most_common(20),
        columns=["단어", "횟수"]
    )

    st.dataframe(
        freq_df,
        use_container_width=True
    )

    st.subheader("☁️ 워드클라우드")

    if len(words) == 0:
        st.warning("워드클라우드를 생성할 단어가 없습니다.")
    else:

        FONT_FILE = "NanumGothic.ttf"

        if not os.path.exists(FONT_FILE):

            try:
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
                    FONT_FILE
                )

            except Exception as e:
                st.error(f"폰트 다운로드 실패: {e}")
                st.stop()

        try:

            wc = WordCloud(
                font_path=FONT_FILE,
                width=1400,
                height=700,
                background_color="white",
                collocations=False
            ).generate(
                " ".join(words)
            )

            fig, ax = plt.subplots(figsize=(14, 7))

            ax.imshow(wc)
            ax.axis("off")

            st.pyplot(fig)

        except Exception as e:
            st.error(f"워드클라우드 생성 실패: {e}")

    st.subheader("⬇️ 댓글 다운로드")

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "youtube_comments.csv",
        "text/csv"
    )
```
