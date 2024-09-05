# vector-victor-rag

# Data
[FAA JO 7110.65AA](https://www.faa.gov/documentLibrary/media/Order/7110.65AA_ATC_Basic_dtd_4-20-23_FINAL.pdf)

# Initial Prototype
[Google Colab Notebook](https://colab.research.google.com/drive/1aslnuPA4klCSXC2SAl3hpJA_W4NnjZ2N?usp=sharing)

# R Shiny App

Enables an SME to easily compare and select the best responses.

`Rscript setup.R`

`Rscript -e "shiny::runApp('app.R')"`

# Linting & Formatting
To lint and format the code using [black](https://black.readthedocs.io/en/stable/) and [ruff](https://docs.astral.sh/ruff/), run:
```
make fix
```