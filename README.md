# vector-victor-rag

# Data
[FAA JO 7110.65AA](https://www.faa.gov/documentLibrary/media/Order/7110.65AA_ATC_Basic_dtd_4-20-23_FINAL.pdf)

# Initial Prototype
[Google Colab Notebook](https://colab.research.google.com/drive/1aslnuPA4klCSXC2SAl3hpJA_W4NnjZ2N?usp=sharing)

# Steps
The notebooks outline the steps that I took to create a retrieval-augmented generation (RAG) implementation.
- [X] Assess if GPT-4o's knowledge of the FAA JO 7110.65AA
- [X] Determine performance metrics to assess RAG implementation
- [X] Create R shiny app for labeling data and work with SME to create labeled dataset
- [X] Extract text, images, and tables from the FAA JO 7110.65AA PDF
- [] Obtain text descriptions for the images and tables from the FAA JO 7110.65AA PDF
- [] Chunk text and generate text embeddings
- [] Put embeddings into a graph database
- [] Create code for retrieval and generation
- [] Create an R shiny app to act as a user interface to the RAG implementation
- [] Test RAG implementation and iterate appropriately

# R Shiny App

Enables an SME to easily compare and select the best responses.

`Rscript setup.R`

`Rscript -e "shiny::runApp('app.R')"`

# Linting & Formatting
To lint and format the code using [black](https://black.readthedocs.io/en/stable/) and [ruff](https://docs.astral.sh/ruff/), run:
```
make fix
```