"""Скрипт для сравнения результатов тестирования RAGAS"""
import json

def compare_results():
    # Загрузка старых результатов (с пустым контекстом)
    with open("evaluation_results.json", "r", encoding="utf-8") as f:
        old_results = json.load(f)
    
    # Загрузка новых результатов (с полным контекстом)
    with open("evaluation_results2.json", "r", encoding="utf-8") as f:
        new_results = json.load(f)
    
    print("=" * 60)
    print("СРАВНЕНИЕ РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ RAGAS")
    print("=" * 60)
    print()
    
    # Сравнение Faithfulness
    old_faith = old_results["faithfulness"]
    new_faith = new_results["faithfulness"]
    
    print("[FAITHFULNESS] (верность контексту):")
    print("-" * 40)
    print(f"Старая версия (description only): {sum(old_faith)/len(old_faith):.4f}")
    print(f"Новая версия (full book info):    {sum(new_faith)/len(new_faith):.4f}")
    print()
    
    for i in range(len(old_faith)):
        change = new_faith[i] - old_faith[i]
        arrow = "UP" if change > 0 else "DOWN" if change < 0 else "="
        print(f"Query {i+1}: {old_faith[i]:.4f} -> {new_faith[i]:.4f} {arrow}")
    print()
    
    # Сравнение Answer Relevancy
    old_rel = old_results["answer_relevancy"]
    new_rel = new_results["answer_relevancy"]
    
    print("[ANSWER RELEVANCY] (релевантность ответа):")
    print("-" * 40)
    print(f"Старая версия (description only): {sum(old_rel)/len(old_rel):.4f}")
    print(f"Новая версия (full book info):    {sum(new_rel)/len(new_rel):.4f}")
    print()
    
    for i in range(len(old_rel)):
        change = new_rel[i] - old_rel[i]
        arrow = "UP" if change > 0 else "DOWN" if change < 0 else "="
        print(f"Query {i+1}: {old_rel[i]:.4f} -> {new_rel[i]:.4f} {arrow}")
    print()
    
    # Анализ контекста
    print("[CONTEXT ANALYSIS]:")
    print("-" * 40)
    
    for i in range(len(old_results["retrieved_contexts"])):
        old_ctx = old_results["retrieved_contexts"][i]
        new_ctx = new_results["retrieved_contexts"][i]
        
        old_empty = sum(1 for c in old_ctx if not c or not c.strip())
        new_empty = sum(1 for c in new_ctx if "Описание:" not in c)
        
        print(f"Query {i+1}:")
        print(f"  Старый контекст: {old_empty}/5 пустых")
        print(f"  Новый контекст: {new_empty}/5 без описания")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    compare_results()

