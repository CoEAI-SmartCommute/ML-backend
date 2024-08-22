import pickle

pickle_file_path = 'array2.pkl'



def import_data():
    with open(pickle_file_path, 'rb') as f:
        accident_data = pickle.load(f)
    return accident_data


a = import_data()
print(max(a['crime_score'].values))
