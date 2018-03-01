# NLPCourseBot
Telegram-bot for NLP/RL courses at MIPT

It can:
* receive questions from students
* receive homeworks (in .zip or .ipynb form)
* provide cross-check interface for homeworks (students check homeworks from other students)
* loading quizzes from json and provide interface for them
    * quiz json also could be obtained from Google Forms (using url or downloaded html) 
    * accepted questions types are following:
        * tests with one right answer
        * tests with multiple right answers
        * question with any possible text answer
        * all questions could contain pictures
* provide cross-check interface for quiz questions with an arbitrary text answer
* provide statistics for homeworks and quizzes in the admin menu
