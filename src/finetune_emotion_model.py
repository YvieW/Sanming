import transformers
assert transformers.__version__ >= '4.36.0', f"Transformers 版本太低: {transformers.__version__}，请升级到 >=4.36.0"
import os
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer


# 设置路径
data_path = os.path.join('data', 'processed_data', 'emotion_data.csv')
model_path = os.path.join('local_model_cache', 'models--IDEA-CCNL--Erlangshen-Roberta-110M-Sentiment')
output_dir = os.path.join('local_model_cache', 'finetuned_emotion_model')
# 加载数据
df = pd.read_csv(data_path) 
df = df[['processed_content', 'label']].dropna()

# 映射标签到数字
label_list = ['sad',  'fear', 'disgust', 'surprise', 'angry', 'neutral','joy', 'positive']
label2id = {label: idx for idx, label in enumerate(label_list)}
id2label = {idx: label for label, idx in label2id.items()}
df['label'] = df['label'].map(label2id)

# 转换为 Hugging Face Dataset
dataset = Dataset.from_pandas(df)

# 加载 tokenizer 和 model
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(
    model_path,
    num_labels=len(label2id),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True
)

# 预处理函数
def preprocess(example):
    return tokenizer(example['processed_content'], truncation=True, padding='max_length', max_length=128)

dataset = dataset.map(preprocess)

# 划分训练/验证集
dataset_split = dataset.train_test_split(test_size=0.1)

# 训练参数
training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=2e-5,
    weight_decay=0.01,
    logging_dir="./logs",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy"
)

# 指标评估函数
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro")
    }

# 创建 Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset_split["train"],
    eval_dataset=dataset_split["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# 训练模型
trainer.train()

# 保存模型和 tokenizer
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)
