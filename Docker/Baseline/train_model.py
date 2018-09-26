from qanta.guesser.tfidf import TfidfGuesser
from qanta.datasets.quiz_bowl import QuizBowlDataset

MODEL_SAVE_DIR = 'tfidf_model'

dataset = QuizBowlDataset(guesser_train=True)
tfidf_guesser = TfidfGuesser(None)
tfidf_guesser.train(dataset.training_data())
tfidf_guesser.save(MODEL_SAVE_DIR)
