docker compose exec postgres \
  psql -U retriever -d repo_retriever


                   Code Repository
                         │
                         ▼
                    RepoScanner
                         │
                         ▼
                 Tree-sitter Parser
             Python / Java / JS / TSX
                         │
                         ▼
                      Symbol[]
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
       PostgreSQL                   Qdrant
     metadata/index         dense + sparse vectors
            │                         │
            ▼                         ▼
      Symbol Search            Hybrid Search
            │                         │
            └────────────┬────────────┘
                         ▼
                    CodeRetriever
                         │
                         ▼
                       Top K