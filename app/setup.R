options(repos = c(CRAN = "https://cloud.r-project.org/"))

install.packages("shiny")
install.packages("DBI")
install.packages("readr")
install.packages("RSQLite")
install.packages("shinythemes")
install.packages("shinyjs")

library(DBI)
library(RSQLite)

conn <- dbConnect(RSQLite::SQLite(), "responses.db")

dbExecute(conn, "
  CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    selected_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
  )
")

dbDisconnect(conn)
