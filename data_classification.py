import pickle

from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sys import argv
from sys import stdout

import darwin_queries
import data_gathering

if __name__ == "__main__":

    data = data_gathering.load_dataset(filepath=argv[1])

    n_samples = data[0]
    n_targets = data[1]

    for s in n_samples:
        print len(s)

    print len(n_samples)
    print n_targets

    print len(data[0]) == len(data[1]) , len(data[0]), len(data[1])

    #pprint(data)

    n_samples_train, n_samples_test, n_targets_train, n_targets_test = train_test_split(n_samples, n_targets, train_size=0.80)

    clf = LinearSVC(random_state=0)

    clf.fit(n_samples, n_targets)

    pickle.dump(clf, open('clf.pkl', 'wb'))

    results = []

    for i in range(0, 15):
        print i
        app_data = data_gathering.eval_app(queries=darwin_queries.DARWIN_QUERIES, qtypes=darwin_queries.QUERY_TYPES,
                                           domain='http://localhost:32775', name='Android Studio.app', evaltime=35, wait=4,
                                           dt=7)
        rez = clf.predict([app_data])
        results += [rez]
        stdout.write(rez)