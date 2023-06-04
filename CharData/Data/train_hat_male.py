# Standard includes
import pickle
import pandas as pd
import string
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sn
from sklearn.metrics import precision_recall_fscore_support, classification_report
from sklearn.model_selection import train_test_split


# Setup pre-processing definitions
stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()


# Helper Functions
def clean(doc):
    stop_free = " ".join([i for i in doc.split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized


# Read data from converted/compiled CSV
df = pd.read_csv("male_data.csv")


# Preview the first 5 lines of the loaded data
print(df.head())

# Data Values: -1 0 1 2
# Convert label column to numeric labels
df.loc[df.Hat == "-1", 'Hat'] = "0"
df.loc[df.Hat == "0", 'Hat'] = "1"
df.loc[df.Hat == "1", 'Hat'] = "2"
df.loc[df.Hat == "2", 'Hat'] = "3"

df["Hat"] = df["Hat"].astype(int)

# Read each document and clean it.
df["AnswerCombined"] = df["AnswerCombined"].apply(clean)


# Lets do some quick analysis
CategoryLabels = list(df["Hat"])
Category0 = CategoryLabels.count(-1)
Category1 = CategoryLabels.count(0)
Category2 = CategoryLabels.count(1)
Category3 = CategoryLabels.count(2)


print(" ")
print("===============")
print("Data Distribution:")
print('Category0 contains:', Category0, float(Category0) / float(len(CategoryLabels)))
print('Category1 contains:', Category1, float(Category1) / float(len(CategoryLabels)))
print('Category2 contains:', Category2, float(Category2) / float(len(CategoryLabels)))
print('Category3 contains:', Category3, float(Category3) / float(len(CategoryLabels)))


Category0_data = df[df['Hat'] == -1]
Category1_data = df[df['Hat'] == 0]
Category2_data = df[df['Hat'] == 1]
Category3_data = df[df['Hat'] == 2]

Category0_train, Category0_test = train_test_split(Category0_data, test_size=0.2)
Category1_train, Category1_test = train_test_split(Category1_data, test_size=0.2)
Category2_train, Category2_test = train_test_split(Category2_data, test_size=0.2)
Category3_train, Category3_test = train_test_split(Category3_data, test_size=0.2)

train = pd.concat([Category0_train, Category1_train, Category2_train, Category3_train])
test = pd.concat([Category0_test, Category1_test, Category2_test, Category3_test])

df['is_train'] = 0
df.loc[train.index, 'is_train'] = 1

training_corpus = train['AnswerCombined'].values
training_labels = train['Hat'].values + 1
test_corpus = test['AnswerCombined'].values
test_labels = test['Hat'].values + 1


# Create TF-IDF Features
tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=5000, stop_words='english')
tfidf = tfidf_vectorizer.fit_transform(training_corpus)
X = tfidf_vectorizer.fit_transform(training_corpus).todense()

featurized_training_data = []
for x in range(0, len(X)):
    tfidFeatures = np.array(X[x][0]).reshape(-1, )
    featurized_training_data.append(tfidFeatures)


# Generate Feature Headers
FeatureNames = []
dimension = X.shape[1]
for x in range(0, dimension):
    FeatureNames.append("TFIDF_" + str(x))

X = tfidf_vectorizer.transform(test_corpus).todense()
featurized_test_data = []
for x in range(0, len(X)):
    tfidFeatures = np.array(X[x][0]).reshape(-1, )
    featurized_test_data.append(tfidFeatures)


# Create final dataframes
TargetNamesStrings = ["0", "1", "2", "3"]
TargetNames = np.asarray([0, 1, 2, 3])

train = pd.DataFrame(featurized_training_data, columns=FeatureNames)
test = pd.DataFrame(featurized_test_data, columns=FeatureNames)
train['categories'] = pd.Categorical.from_codes(training_labels, TargetNames)
test['categories'] = pd.Categorical.from_codes(test_labels, TargetNames)

# Show the number of observations for the test and training dataframes
print(" ")
print("===============")
print("Fold Information: ")
print('Number of observations in the training data:', len(train))
print('Number of features generated:', str(dimension))
print(" ")
print('Number of observations in the test data:', len(test))


# Create a list of the feature column's names
features = train.columns[:dimension]


# Create a random forest classifier. By convention, clf means 'classifier'
clf = RandomForestClassifier(n_jobs=-1, class_weight="balanced")


# Train the classifier to take the training features and learn how they relate to the training y (the stressors)
clf.fit(train[features], train['categories'])


# Apply the classifier we trained to the test data (which, remember, it has never seen before)
preds = clf.predict(test[features])


# View the PREDICTED stressors for the first five observations
print(" ")
print("===============")
print("Example Prediction: ")
print(preds[0:5])


# View the ACTUAL stressors for the first five observations
print(" ")
print("===============")
print("Actual: ")
print(str(test['categories'].head()))


# Create confusion matrix
print(" ")
print("===============")
print("Confusion Matrix: ")
print(" ")
confusion_matrix = pd.crosstab(test['categories'], preds, rownames=['Actual Categories'], colnames=['Predicted Categories'])
print(str(pd.crosstab(test['categories'], preds, rownames=['Actual Categories'], colnames=['Predicted Categories'])))


# Show confusion matrix in a separate window
sn.set(font_scale=1.4)#for label size
g = sn.heatmap(confusion_matrix, annot=True,annot_kws={"size": 12}, cmap="YlGnBu", cbar=False)# font size
bottom, top = g.get_ylim()
g.set_ylim(bottom + 0.5, top - 0.5)
plt.show()


# Precision, Recall, F1
print(" ")
print("Precision, Recall, Fbeta Stats: ")
print('Macro:  ', precision_recall_fscore_support(test['categories'], preds, average='macro'))
print('Micro:  ', precision_recall_fscore_support(test['categories'], preds, average='micro'))
print('Weighted', precision_recall_fscore_support(test['categories'], preds, average='weighted'))
print(classification_report(test['categories'], preds, target_names=TargetNamesStrings))


# View a list of the features and their importance scores
print(" ")
print("===============")
print("Top Features: ")
print(str(list(zip(train[features], clf.feature_importances_))))


# save the model to disk
filename = 'finalized_model.sav'
pickle.dump(clf, open(filename, 'wb'))
exit()