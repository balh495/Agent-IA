# A propos

La solution JO-Chatbot est un agent IA de chatbot spécialisé au contexte des lois et decrets de la République du Congo.


Pour cela, un modèle llm a été spécialisé dans ce contexte par une approche RAG afin d'utiliser le modèle `llama3.2 de Meta` qu'on a spécialisé dans notre contexte.

# Fonctionnement

1. Récupération des fichiers sur le journal officiel
2. Extraction du contenu de ces fichiers avec l'ocr paddle
3. Stockage du contenu dans une base de données vectorielle
4. Injection du contenu extrait de la base vectorielle dans les requêtes au modèle 

La mise en place du lab se fait avec le server de modèle Ollama qui permet d'obtenir des modèle en version compressée. Dans notre cas, le modèle llama3.2 qui fait plus de 10 Go, fait moins de 2 Go.