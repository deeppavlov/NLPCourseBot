# NLPCourseBot
Telegram-bot for NLP/RL courses at MIPT

## It can work with quizzes, homeworks and student questions

* receive questions from students
* receive homeworks (in any archive or .ipynb form)
* provide cross-check interface for homeworks (students check homeworks from other students)
* provide statistics for homeworks and quizzes in the admin menu

### Quizzes
* loading quizzes from json and provide interface for them
    * quiz json also could be obtained from Google Forms (using url or downloaded html) 
    * accepted question types are following:
        * tests with one right answer
        * tests with multiple right answers
        * question with any possible text answer
        * all questions could contain pictures
    * autocheck for test questions
    * provide cross-check interface for quiz questions with an arbitrary text answer
