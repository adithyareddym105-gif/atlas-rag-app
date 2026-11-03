# RAG App V2: Overview and User Workflow

The Atlas RAG App V2 is a local web application for asking questions about a selected collection of Markdown and plain-text documents. Its main purpose is to produce answers grounded in the uploaded corpus and to show the source passages that were supplied to the language model. A source reference includes the document name, chunk number, score, and excerpt so the user can inspect the evidence instead of treating the answer as automatically correct.

The application accepts Markdown files with the .md extension and plain-text files with the .txt extension. Uploads are stored in the local data/documents.json file. A user can add documents, inspect the available collection, select which documents should be used for a question, and delete documents that are no longer needed. The built-in Kestrel knowledge base is separate from user-uploaded documents and contains five Markdown files.

The main workflow is: choose a corpus, select documents when using the custom corpus, set chunk size and overlap, enter a question, and choose the number of retrieved chunks. The server searches the selected corpus, sends the retrieved passages to the configured language model, and returns the answer together with source references. The model instruction says to use only the supplied context and to state when the documents do not contain enough information.

The app includes an Evaluation view for running a fixed question set and a Words Analytics view for inspecting corpus vocabulary and question terms. An additional /about route exists for the assignment requirement; it is intentionally not linked from the main interface. The application is designed as a coursework prototype and should not be treated as a production knowledge-management system.

When no language-model key or model name is configured, the question-answering endpoint returns a controlled configuration error instead of attempting a request. Evaluation and lexical retrieval can still be run locally without an external language-model call.
