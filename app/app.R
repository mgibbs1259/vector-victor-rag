library(shiny)
library(DBI)
library(RSQLite)
library(readr)
library(shinythemes)
library(shinyjs)

ui <- fluidPage(
  theme = shinytheme("darkly"),
  titlePanel("Select the Best Response"),
  fluidRow(
    column(12,
      useShinyjs(),
      style = "padding: 20px;",
      uiOutput("question_ui"),
      br(),
      uiOutput("response_buttons"),
      br(), br(),
      uiOutput("completion_message")
    )
  ),
  tags$style(HTML("
    .btn-primary {
        background-color: #0056b3;  /* Darker shade of blue */
        border-color: #004085;      /* Darker border color */
        white-space: normal;        /* Allow text to wrap */
        word-wrap: break-word;      /* Ensure long words break */
        text-align: center;         /* Center text inside buttons */
        padding: 10px;              /* Add padding inside buttons */
        min-width: 150px;           /* Ensure buttons are wide enough */
    }
    .btn-primary:hover {
        background-color: #004085;  /* Even darker on hover */
        border-color: #003057;      /* Darker border color on hover */
    }
    .btn-default {
        background-color: #525151;  /* Slightly darker gray */
        border-color: #b0b0b0;      /* Slightly darker gray border */
        white-space: normal;        /* Allow text to wrap */
        word-wrap: break-word;      /* Ensure long words break */
        text-align: center;         /* Center text inside buttons */
        padding: 10px;              /* Add padding inside buttons */
        min-width: 150px;           /* Ensure buttons are wide enough */
    }
    .btn-default:hover {
        background-color: #c0c0c0;  /* Even darker on hover */
        border-color: #a0a0a0;      /* Darker border color on hover */
    }
    .question {
        margin-top: 20px;
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        text-align: center;         /* Center the question text */
        word-wrap: break-word;      /* Ensure long words break */
        padding: 0 10px;           /* Add padding for small screens */
    }
    .completion-message {
        font-size: 30px;            /* Adjusted font size for visibility */
        font-weight: bold;
        color: #28a745;  /* Green color for completion message */
        text-align: center;  /* Center text horizontally */
        margin-top: 20px;    /* Add margin on top */
        word-wrap: break-word; /* Ensure long words break */
    }
    .button-container {
        display: flex;           /* Align buttons in a row */
        justify-content: center; /* Center buttons horizontally */
        gap: 20px;               /* Space between buttons */
        flex-wrap: wrap;         /* Allow buttons to wrap on smaller screens */
    }
    .centered-button {
        display: flex;
        justify-content: center;
        margin-top: 30px;   /* Add more space above the button */
    }
    .centered-button-container {
        display: flex;
        justify-content: center;
        margin-top: 30px;   /* Add space above the previous button */
    }
  ")),
  tags$script(HTML("
    function updateButtonStyles(response1Selected, response2Selected) {
      var response1 = document.getElementById('response1');
      var response2 = document.getElementById('response2');
      if (response1Selected) {
        response1.classList.add('btn-primary');
        response1.classList.remove('btn-default');
      } else {
        response1.classList.add('btn-default');
        response1.classList.remove('btn-primary');
      }
      if (response2Selected) {
        response2.classList.add('btn-primary');
        response2.classList.remove('btn-default');
      } else {
        response2.classList.add('btn-default');
        response2.classList.remove('btn-primary');
      }
    }
    Shiny.addCustomMessageHandler('updateButtonStyles', function(message) {
      updateButtonStyles(message.response1Selected, message.response2Selected);
    });
  "))
)

server <- function(input, output, session) {
  con <- dbConnect(RSQLite::SQLite(), "responses.db")
  
  # Create table if it does not exist
  dbExecute(con, "CREATE TABLE IF NOT EXISTS responses (question TEXT, selected_response TEXT)")
  
  # Load CSV data
  data <- read_csv("questions_responses.csv")
  
  # Reactive values to keep track of the current question, index, and responses
  rv <- reactiveValues(
    question_index = 1,
    question = NULL,
    responses = rep(NA, nrow(data)),  # Track selected responses
    is_last_question = FALSE
  )
  
  # Update question and buttons based on the current index
  observe({
    if (nrow(data) > 0 && rv$question_index <= nrow(data)) {
      current_row <- rv$question_index
      rv$question <- data$question[current_row]
      rv$is_last_question <- (rv$question_index == nrow(data))
      
      updateActionButton(session, "response1", label = data$response_1[current_row])
      updateActionButton(session, "response2", label = data$response_2[current_row])
      
      # Show question and response buttons
      output$question_ui <- renderUI({
        div(class = "question", h3(rv$question))
      })
      
      output$response_buttons <- renderUI({
        tagList(
          div(class = "button-container",
              actionButton("response1", "Response 1", class = "btn btn-default btn-lg"),
              actionButton("response2", "Response 2", class = "btn btn-default btn-lg")
          ),
          div(class = "centered-button-container",
              if (rv$question_index > 1) actionButton("prev_question", "Previous", class = "btn btn-default btn-lg")
          )
        )
      })
      
      # Update button styles based on the previously selected response
      session$sendCustomMessage(type = 'updateButtonStyles', 
                                message = list(response1Selected = rv$responses[rv$question_index] == "Response 1",
                                               response2Selected = rv$responses[rv$question_index] == "Response 2"))
    }
  })
  
  # Output the completion message if all questions have been answered and user navigates past the last question
  output$completion_message <- renderUI({
    if (rv$question_index > nrow(data)) {
      tagList(
        div(class = "completion-message", "All Questions Completed"),
        div(class = "centered-button-container",
            actionButton("prev_question_after_complete", "Previous", class = "btn btn-default btn-lg")
        )
      )
    } else {
      NULL
    }
  })

  # Button click event for response 1
  observeEvent(input$response1, {
    if (!is.null(rv$question)) {
      rv$responses[rv$question_index] <- "Response 1"
      dbExecute(con, "INSERT OR REPLACE INTO responses (question, selected_response) VALUES (?, ?)",
                params = list(rv$question, "Response 1"))
      
      if (rv$is_last_question) {
        rv$question_index <- rv$question_index + 1
        output$question_ui <- renderUI({ NULL })
        output$response_buttons <- renderUI({ NULL })
        output$completion_message <- renderUI({
          tagList(
            div(class = "completion-message", "All Questions Completed"),
            div(class = "centered-button-container", actionButton("prev_question_after_complete", "Previous", class = "btn btn-default btn-lg"))
          )
        })
      } else {
        rv$question_index <- rv$question_index + 1
      }
      session$sendCustomMessage(type = 'updateButtonStyles', 
                                message = list(response1Selected = rv$responses[rv$question_index] == "Response 1",
                                               response2Selected = rv$responses[rv$question_index] == "Response 2"))
    }
  })

  # Button click event for response 2
  observeEvent(input$response2, {
    if (!is.null(rv$question)) {
      rv$responses[rv$question_index] <- "Response 2"
      dbExecute(con, "INSERT OR REPLACE INTO responses (question, selected_response) VALUES (?, ?)",
                params = list(rv$question, "Response 2"))
      
      if (rv$is_last_question) {
        rv$question_index <- rv$question_index + 1
        output$question_ui <- renderUI({ NULL })
        output$response_buttons <- renderUI({ NULL })
        output$completion_message <- renderUI({
          tagList(
            div(class = "completion-message", "All Questions Completed"),
            div(class = "centered-button-container", actionButton("prev_question_after_complete", "Previous", class = "btn btn-default btn-lg"))
          )
        })
      } else {
        rv$question_index <- rv$question_index + 1
      }
      session$sendCustomMessage(type = 'updateButtonStyles', 
                                message = list(response1Selected = rv$responses[rv$question_index] == "Response 1",
                                               response2Selected = rv$responses[rv$question_index] == "Response 2"))
    }
  })
  
  # Navigate to the previous question
  observeEvent(input$prev_question, {
    if (rv$question_index > 1) {
      rv$question_index <- rv$question_index - 1
      rv$question <- data$question[rv$question_index]
      
      session$sendCustomMessage(type = 'updateButtonStyles', 
                                message = list(response1Selected = rv$responses[rv$question_index] == "Response 1",
                                               response2Selected = rv$responses[rv$question_index] == "Response 2"))
      
      output$question_ui <- renderUI({
        div(class = "question", h3(rv$question))
      })
      
      output$response_buttons <- renderUI({
        tagList(
          div(class = "button-container",
              actionButton("response1", "Response 1", class = "btn btn-default btn-lg"),
              actionButton("response2", "Response 2", class = "btn btn-default btn-lg")
          ),
          div(class = "centered-button-container",
              actionButton("prev_question", "Previous", class = "btn btn-default btn-lg")
          )
        )
      })
      
      output$completion_message <- renderUI({
        NULL
      })
    }
  })

  # Navigate to the previous question after completion message
  observeEvent(input$prev_question_after_complete, {
    if (rv$question_index > 1) {
      rv$question_index <- rv$question_index - 1
      rv$question <- data$question[rv$question_index]
      
      session$sendCustomMessage(type = 'updateButtonStyles', 
                                message = list(response1Selected = rv$responses[rv$question_index] == "Response 1",
                                               response2Selected = rv$responses[rv$question_index] == "Response 2"))
      
      output$question_ui <- renderUI({
        div(class = "question", h3(rv$question))
      })
      
      output$response_buttons <- renderUI({
        tagList(
          div(class = "button-container",
              actionButton("response1", "Response 1", class = "btn btn-default btn-lg"),
              actionButton("response2", "Response 2", class = "btn btn-default btn-lg")
          ),
          div(class = "centered-button-container",
              actionButton("prev_question", "Previous", class = "btn btn-default btn-lg")
          )
        )
      })
      
      output$completion_message <- renderUI({
        NULL
      })
    }
  })

  onStop(function() {
    dbDisconnect(con)
  })
}

shinyApp(ui = ui, server = server)
