import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
#from sklearn.cross_validation import train_test_split

from convRBM import CRBM
import getData as dataRead
import trainingObserver as observer

import numpy as np
import random
import time
from datetime import datetime
import cPickle
import theano
import os

########################################################
# SET THE HYPER PARAMETERS
epochs = 900
cd_k = 5
learning_rate = 0.00001
motif_length = 11
number_of_motifs = 2
batch_size = 100
pooling_factor = 5

train_test_ratio = 0.01
USE_WHOLE_DATA = True
########################################################



# read the data and split it
seqReader = dataRead.SeqReader()
allSeqs = seqReader.readSequencesFromFile('../data/wgEncodeAwgDnaseUwAg10803UniPk.fa')

if USE_WHOLE_DATA:
	data = allSeqs
else:
	data = [allSeqs[random.randrange(0,len(allSeqs))] for i in range(2000)]

# no train_test_split necessary
per=np.random.permutation(len(data))
itest=per[:int(len(data)*train_test_ratio)]
itrain=per[int(len(data)*train_test_ratio):]
#train_set, test_set = train_test_split(data, test_size=train_test_ratio)
#print "Training set size: " + str(len(train_set))
#print "Test set size: " + str(len(test_set))

# convert raw sequences to one hot matrices
start = time.time()
trainingData = np.array([data[i] for i in itrain])
testingData = np.array([data[i] for i in itest])
print "Conversion of test set in (in ms): " + str((time.time()-start)*1000)

# construct the model
hyper_params = {'number_of_motifs':number_of_motifs,
				'motif_length':motif_length,
				'learning_rate':learning_rate,
				'pooling_factor':pooling_factor,
				'epochs':epochs,
				'cd_k':cd_k,
				'batch_size':batch_size
}
learner = CRBM(hyperParams=hyper_params)

# add the observers for free energy (test and train)
free_energy_observer = observer.FreeEnergyObserver(learner, testingData, "Free Energy Testing Observer")
learner.addObserver(free_energy_observer)
free_energy_train_observer = observer.FreeEnergyObserver(learner, trainingData, "Free Energy Training Observer")
learner.addObserver(free_energy_train_observer)

# add the observers for reconstruction error (test and train)
reconstruction_observer = observer.ReconstructionErrorObserver(learner, testingData, "Reconstruction Error Testing Observer")
learner.addObserver(reconstruction_observer)
reconstruction_observer_train = observer.ReconstructionErrorObserver(learner, trainingData, "Reconstruction Error Training Observer")
learner.addObserver(reconstruction_observer_train)

# add the observer of the motifs during training (to look at them afterwards)
param_observer = observer.ParameterObserver(learner, trainingData)
learner.addObserver(param_observer)

# add the motif hit scanner
motif_hit_observer = observer.MotifHitObserver(learner, testingData)
learner.addObserver(motif_hit_observer)
print "Data mat shape: " + str(trainingData.shape)


# perform training
start = time.time()
learner.trainModel(trainingData)
print "Training of " + str(trainingData.shape[0]) + " performed in: " + str(time.time()-start) + " seconds."

# save trained model to file
date_string = datetime.now().strftime("%Y_%m_%d_%H_%M")
os.mkdir('../../training/' + date_string)
file_name = "../../training/" + date_string + "/model.pkl"
print "Saving model to " + str(file_name)
learner.saveModel(file_name)

# plot
plt.subplot(2,1,1)
plt.ylabel('Free energy function')
plt.title(str(epochs) + " epo " + str(motif_length) + " kmers " + str(number_of_motifs) + " motifs_CD "+str(cd_k)+".png")
plt.plot(free_energy_observer.scores)
plt.plot(free_energy_train_observer.scores)

plt.subplot(2,1,2)
plt.ylabel('Reconstruction error on dataset')
plt.xlabel('Number Of Epoch')
plt.title('Reconstruction Error')
plt.plot(reconstruction_observer.scores)
plt.plot(reconstruction_observer_train.scores)

# save plot to file
file_name_plot = "../../training/" + date_string + "/errorPlot.png"
plt.savefig(file_name_plot)
