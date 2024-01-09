# ENTest

[ENTest](https://entest.fly.dev/) is a simple English vocab quiz that uses statistics and machine learning to accurately and quickly predict a user's vocab level. Testing using preexisting tests take forever (100s of questions) and/or are terribly innaccurate so I made this.

ENTest is a fork from [JiKen](https://github.com/Ambiwlans/JiKen) a japanese kanji testing site with the same functionality.

## Host/Location

# https://entest.fly.dev/
* Using Fly.io as a webhost, Planetscale for MySQL, Redislabs for sessions.

## Math

First thing to know to understand why this works so well is that word usage (and recognition) is not flat/random but has a relatively normal distribution and follows [Ziph's Law](https://en.wikipedia.org/wiki/Zipf%27s_law). This allows us to make relatively sensible predictions of people's knowledge using a sigmoid function.

There are two main algorithms worth noting. 

One predicts how many words you know (the graph) based on your answers. This is a Nelder-Mead regression algo with custom regularization: giving a lot of weight to the initial values (safe assumption until data is collected), L2 reg (to avoid traps), some penalty to change between questions to give users a smooth experience. I also do bias correction as per https://cs.nyu.edu/~mohri/pub/bias.pdf since the questions selected are not random. No formal tuning methods were use, everything was done by hand until it felt good (the tuning target was to meet user expectations rather than simply being mathematically accurate).

The other algorithm is an online one that continuously reranks the difficulty of every word for future testing. If 100 people know "avatar" but don't know "churl" then the algorithm will shuffle the ranks around so that "churl" is ranked lower, "avatar" higher. This is called a Learning to rank algorithm: https://mlexplained.com/2019/05/27/learning-to-rank-explained-with-code/. Of course, this was again made more complicated by having biased sample selection. In simple terms, you can think of this as similar to a chess elo ranking system.

I also used ML to predict the error bars, simply feeding past test variability from final values and question number (using ~50 tests). I may revisit this with a more serious algorithm once I have more data to feed and can avoid the risk of overfitting.

## Built With

* Flask
* SQLAlchemy (MySQL)
* Redis (for sessions/ buffering)
* APscheduler
* Bootstrap
* ChartJS
* Genanki https://github.com/kerrickstaley/genanki (to generate anki files)
* Datatables.js (for the missed word list)

## Contact/Bugs

You can report bugs here or contact me via [reddit](https://www.reddit.com/message/compose?to=%2Fu%2FAmbiwlans&subject=ENTest), [twitter](https://twitter.com/Ambiwlans1) #entest, or [e-mail](mailto:udp.castellani@gmail.com). 

## Licensing/Contribute

Shoot me a message if you want to do something with this code.

## Acknowledgments

* Huge credit to [GCIDE](https://gcide.gnu.org.ua/) for the initial dictionary data
