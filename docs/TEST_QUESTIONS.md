# Comprehensive Test Questions for RAG System

Based on the actual documents in the corpus (Bengali, Urdu, and Chinese PDFs), here are comprehensive test questions that demonstrate the system's capabilities:

## Bengali Document Questions (Research Nirdeshika - Research Guidelines)

### Basic Retrieval Questions:
1. **বাংলায়: গবেষণা নির্দেশিকায় কী কী বিষয় আছে?**
   - English: What topics are covered in the research guidelines?
   - Expected: Should retrieve information about research guidelines from the Cabinet Division

2. **What is the maximum budget allowed for research projects according to the guidelines?**
   - Expected: Should find specific amounts mentioned (৫০,০০,০০০/- টাকা)

3. **মন্ত্রিপরিষদ বিভাগের গবেষণা নির্দেশিকা কখন সংশোধিত হয়েছে?**
   - English: When was the Cabinet Division's research guideline revised?
   - Expected: এপ্রিল ২০২৪ (April 2024)

### Complex Questions (Query Decomposition):
4. **What are the policy input requirements and funding limits for government research projects in Bangladesh?**
   - Tests: Hybrid retrieval + query decomposition
   - Expected: Multiple chunks about policy requirements and budget limits

5. **Compare the research approval process and budget allocation mentioned in the guidelines**
   - Tests: Multi-hop reasoning, semantic search

## Urdu Document Questions (Employment Extensions & Notifications)

### Basic Retrieval:
6. **عارضی ملازمین کی ملازمت کی مدت کب تک بڑھائی گئی ہے؟**
   - English: Until when has the employment period of adhoc employees been extended?
   - Expected: 31.10.2024 تک

7. **What is the reference number of the notification regarding extension of adhoc employees?**
   - Expected: جموں وکشمیر/2024/961-1060

8. **Who issued the order for the extension of adhoc and contractual employees?**
   - Expected: Governor of Jammu and Kashmir (صدر آزاد جموں وکشمیر)

### Complex Questions:
9. **What are the conditions and procedures for extending temporary government employment in Jammu & Kashmir?**
   - Tests: Context understanding, semantic search
   
10. **List all the officials mentioned in the distribution list of the employment extension order**
    - Tests: Structured information extraction

## Chinese Document Questions (People's Congress Documents)

### Basic Retrieval:
11. **这个文件是关于什么的？** (What is this document about?)
    - Expected: Information about People's Congress (人大)

12. **文件中提到了哪些重要的会议或事件？**
    - English: What important meetings or events are mentioned in the document?
    - Expected: References to Central Committee meetings (中央会议)

13. **What is the publication date mentioned in the Chinese document?**
    - Expected: 2022/2/5 (from one of the documents)

### Complex Questions:
14. **Explain the main political consensus mentioned in the People's Congress document**
    - Tests: Semantic understanding, context retrieval
    - Expected: Information about "两个确立" and "两个维护"

15. **What are the key responsibilities and functions of the National People's Congress as described?**
    - Tests: Long-form answer generation, multiple chunk fusion

## Cross-Lingual Questions

### Multilingual Retrieval:
16. **What types of administrative documents are available in the database across all languages?**
    - Tests: Language-agnostic retrieval, metadata filtering

17. **Compare the bureaucratic processes described in the Bengali research guidelines and the Urdu employment notification**
    - Tests: Cross-document reasoning, multilingual understanding

18. **Find all documents related to government policy or regulations**
    - Tests: Semantic search across languages

## Advanced RAG Testing Questions

### Metadata Filtering:
19. **Show me only Bengali language documents about research**
    - Tests: Language filtering + semantic search

20. **Find Urdu documents issued in 2024**
    - Tests: Metadata filtering + date extraction

### Query Decomposition:
21. **What are the similarities and differences between research funding processes in Bengali documents and employment procedures in Urdu documents?**
    - Tests: Complex query decomposition, multi-document reasoning

22. **Analyze the administrative hierarchy and approval processes mentioned across all documents**
    - Tests: Multi-hop reasoning, entity extraction

### Reranking & Relevance:
23. **Find the most relevant information about government employee contract extensions**
    - Tests: Reranking, relevance scoring

24. **What are the specific dates, amounts, and reference numbers mentioned in administrative notifications?**
    - Tests: Precision retrieval, structured information extraction

### Chat Memory:
25. **First: "Tell me about research guidelines"**
    **Then: "What are the budget limits?" (requires memory)**
    - Tests: Context-aware follow-up, chat memory

26. **First: "What is the employment extension document about?"**
    **Then: "Who issued this order?" (requires memory)**
    - Tests: Coreference resolution, memory-based QA

## Stress Test Questions

### Long Context:
27. **Provide a comprehensive summary of all government procedures, policies, and regulations mentioned across Bengali, Urdu, and Chinese documents**
    - Tests: Large context handling, summarization

### Specific Detail Retrieval:
28. **What is the exact reference number (রেফারেন্স নম্বর) mentioned in the Bengali research document?**
    - Tests: Exact match retrieval, precision

29. **List all monetary amounts mentioned in any document with their context**
    - Tests: Numerical information extraction, BM25 keyword search

### No Answer Scenarios:
30. **What is the weather forecast for next week?**
    - Tests: Graceful handling of unanswerable questions

31. **Explain quantum computing algorithms**
    - Tests: Out-of-domain query handling

## Expected System Behaviors

For each question above, the system should:
1. ✅ **Retrieve relevant chunks** from the appropriate language documents
2. ✅ **Show retrieval scores** (semantic + BM25 hybrid)
3. ✅ **Display reranked results** with improved relevance
4. ✅ **Generate accurate answers** using Ollama/Gemini
5. ✅ **Cite sources** with document names and page numbers
6. ✅ **Handle memory** for multi-turn conversations
7. ✅ **Filter by language** when specified
8. ✅ **Decompose complex queries** into sub-queries when needed

## Evaluation Criteria

### Retrieval Quality:
- **Precision**: Top results should be relevant
- **Recall**: Should find all relevant documents
- **Language Accuracy**: Correct language detection and filtering

### Answer Quality:
- **Accuracy**: Answers match document content
- **Completeness**: Addresses all parts of the question
- **Citation**: Proper source attribution

### System Performance:
- **Speed**: Response time < 3 seconds for simple queries
- **Robustness**: Handles edge cases gracefully
- **Memory**: Maintains context across turns

## Priority Test Sequence

### Phase 1: Basic Functionality (Questions 1-5, 6-8, 11-13)
- Test: Basic retrieval in each language
- Expected: 90%+ accuracy

### Phase 2: Advanced Features (Questions 14-18, 21-24)
- Test: Query decomposition, reranking, cross-lingual
- Expected: 80%+ accuracy

### Phase 3: Edge Cases (Questions 25-31)
- Test: Memory, precision, out-of-domain
- Expected: Graceful degradation, no crashes

This comprehensive test suite ensures the RAG system demonstrates:
- ✅ Multilingual capability (Bengali, Urdu, Chinese)
- ✅ Hybrid retrieval (semantic + keyword)
- ✅ Query decomposition for complex questions
- ✅ Reranking for improved relevance
- ✅ Chat memory for multi-turn conversations
- ✅ Metadata filtering
- ✅ Production-ready error handling

