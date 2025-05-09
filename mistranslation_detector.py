import openai
import pandas as pd
import os
from datetime import datetime

# エクセルファイルのパス（適宜変更）
excel_path = "test_trans.xlsx"

# 環境変数からAPIキーを取得
api_key = os.getenv("OPENAI_API_KEY")

# APIキーを設定
openai.api_key = api_key

# ファイル名用のタイムスタンプを生成（秒単位で一意に）
start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 秒まで含めて一意に

# GPTの応答をログファイルに追記保存（固定タイムスタンプで一括管理）
def log_response(content, source_text=None, id_number=None, timestamp=start_timestamp):
    log_filename = f"gpt_log_{timestamp}.txt"
    log_path = os.path.join(os.path.dirname(__file__), log_filename)
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("==== GPT RESPONSE START ====\n")
        if id_number is not None:
            f.write(f"ID: {id_number}\n")
        if source_text:
            f.write(f"Source: {source_text}\n")
        f.write(content + "\n")
        f.write("==== GPT RESPONSE END ====\n\n")

# 入力用Excelファイル（翻訳リスト）を読み込む
df = pd.read_excel(excel_path)

# 翻訳の正確性チェックとバックトランスレーションを同時に行う関数
def check_and_back_translate(source, translation, id_number):
    prompt = (
        f"Check if the following translation is correct for the given English sentence. "
        f"Consider both meaning and grammar. "
        f"If the translation is correct, respond 'Correct'. If it is incorrect, respond 'Incorrect' followed by a brief explanation of why it is incorrect (e.g., meaning difference, grammatical error, or unnatural phrasing).\n\n"
        f"Then, translate the given translation back into English as literally and accurately as possible, preserving the original meaning, even if the English sounds a bit unnatural. Do not paraphrase or add interpretation.\n\n"
        f"English: {source}\n"
        f"Translation: {translation}\n\n"
        f"Respond in the following format:\n"
        f"Check: <Correct or Incorrect + explanation>\n"
        f"Back Translation: <translated sentence>"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # 一貫性と正確性を高める
        top_p=0.1,        # 一貫性をさらに高める
        max_tokens=150     # 説明を短く制限
    )

    content = response["choices"][0]["message"]["content"]

# 応答をログファイルに保存（同じタイムスタンプでまとめる）
    log_response(content, source, id_number, start_timestamp)

# 応答内容をフォーマットに従ってシンプルに抽出（Check と Back Translation）
    check_line = ""
    back_translation_line = ""

    for line in content.splitlines():
        if line.startswith("Check:"):
            check_line = line[len("Check:"):].strip()
        elif line.startswith("Back Translation:"):
            back_translation_line = line[len("Back Translation:"):].strip()

    return check_line, back_translation_line

# 各行に対してチェックとバックトランスレーションを実行し、列に追加
df[['Check', 'Back Translation']] = df.apply(
    lambda row: pd.Series(check_and_back_translate(row["Source"], row["Translation"], row["ID"])), axis=1
)

# SourceとBack Translationを比較して意味の差を評価する関数
def compare_source_and_back_translation(source, back_translation):
    prompt = (
        f"Evaluate how closely the meanings of the following two English sentences match. "
        f"Ignore minor grammatical, stylistic, or punctuation differences and focus only on meaning. "
        f"If both convey exactly the same meaning, respond with only 'Same'. "
        f"If both convey a slightly different meaning (e.g., same core meaning but different nuance, tone, or word choice, such as 'go' vs 'visit' or 'big' vs 'large'), respond with 'Minor Mismatch:' followed by a short description how it is different. "
        f"If both convey a totally different meaning, respond with 'Major Mismatch:' followed by a short description how it is different. "
        f"Consider the following cases as 'Major Mismatch' due to their high importance in meaning: "
        f"1. Differences in numerical values (e.g., '3' vs '5', '10%' vs '20%'), "
        f"2. Differences in units of measurement that imply a significant change (e.g., '3cm' vs '3-inch' for length, '5kg' vs '5lb' for weight, '60km/h' vs '60mph' for speed), "
        f"3. Differences in tense, location, or subject of action (e.g., 'I went' vs 'I will go', 'park' vs 'library', 'he' vs 'she'), "
        f"4. Any factual discrepancy that significantly alters the interpretation of the sentence, including the omission of information that provides critical context or impacts the intended meaning (e.g., omitting details that indicate quality, priority, or specific attributes). "
        f"5. Differences in proper nouns, such as brand names, product names, personal names, service names or place names (e.g., 'Microsoft Edge' vs 'Edge of Microsoft' or 'Google' vs 'Goggle'), even if partially similar. "
        f"However, if the difference is only in nuance, tone, or word choice without changing the core meaning, it should be 'Minor Mismatch'.\n\n"
        f"Source: {source}\n"
        f"Back Translation: {back_translation}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # 一貫性と正確性を高める
        top_p=0.1,        # 一貫性をさらに高める
        max_tokens=100     # 説明を短く制限
    )

    return response["choices"][0]["message"]["content"]

# 比較結果（意味の一致度）をSource Comparison列に保存
df["Source Comparison"] = df.apply(
    lambda row: compare_source_and_back_translation(row["Source"], row["Back Translation"]), axis=1
)

# Risk Scoreを計算する関数
def calculate_risk_score(row):
    # Check列に基づくスコア
    if row["Check"].startswith("Correct"):
        check_score = 0
    else:  # Incorrectの場合
        check_score = 2
    
    # Source Comparison列に基づくスコア
    if row["Source Comparison"].startswith("Same"):
        comparison_score = 0
    elif row["Source Comparison"].startswith("Minor Mismatch"):
        comparison_score = 1
    else:  # Major Mismatchの場合
        comparison_score = 2
    
    # 合計スコアを返す
    return check_score + comparison_score

# 各行にリスクスコアを計算して列として追加
df["Risk Score"] = df.apply(calculate_risk_score, axis=1)

# チェック結果を新しいExcelファイルに保存
df.to_excel("test_trans_done.xlsx", index=False)
print("Saved results to 'test_trans_done.xlsx'")
