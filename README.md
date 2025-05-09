# Mistranslation-Detector

A Python-based tool for detecting potential mistranslations between source and translated texts using OpenAI's GPT models.

## 📄 Overview

This tool reads an Excel file (`test_trans.xlsx`) containing pairs of source and translated texts, and evaluates translation quality **in two ways**:

1. **Direct Evaluation**: Assesses the translated sentence directly.
2. **Back Translation Comparison**: Translates the translation back into the source language and compares it with the original.

Each pair is scored and classified (e.g., "Match", "Minor mismatch", "Major mismatch"), and a total risk score is generated.

## 🔧 Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

Required libraries:

- openai
- pandas
- openpyxl

## 📁 Input File Format

The tool expects an Excel file named `test_trans.xlsx` with the following structure:

| Column | Header            | Description                                                                                                                                |
| ------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| A      | ID                | A unique identifier for each translation pair                                                                                              |
| B      | Source            | The original text to be translated                                                                                                         |
| C      | Translation       | The translated version of the source text                                                                                                  |
| D      | Check             | Direct evaluation result (e.g., Correct / Incorrect)                                                                                       |
| E      | Back Translation  | GPT's back-translated version of the translation                                                                                           |
| F      | Source Comparison | Comparison between the source and back translation                                                                                         |
| G      | Risk Score        | Numerical score reflecting the severity of mistranslation (e.g., 0–4, where higher values indicate a greater likelihood of mistranslation) |

Only columns A, B, and C are required as input. The remaining columns (D–G) will be filled by the script.

## 🚀 How to Run

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=your-api-key-here
```

Then run the script:

```bash
python mistranslation_detector.py
```

- Analyze each translation pair
- Log the results with timestamps and IDs
- Output mismatch statistics and an overall risk score

> 💡 **Note**: The script currently uses the `gpt-4o-mini` model. Using more advanced models like `gpt-4` or `gpt-4o` can potentially improve detection accuracy, especially for nuanced or complex translations.

## 📝 Output

- A log file named `gpt_log_YYYYMMDD_HHMMSS.txt` will be generated in the working directory.
- A result Excel file named `test_trans_done.xlsx` will also be generated, containing the original input along with evaluation results in columns D–G.

## 📌 Notes

- Best suited for lightweight, small-scale translation evaluation.
- Logic is designed for clarity and easy customization.
- Evaluation outputs are in English ("Match", "Minor mismatch", etc.).
- This tool does not modify the original input file. All output is written to a separate log and result file.

## 📚 License

MIT License

---

Created by monta-gh
