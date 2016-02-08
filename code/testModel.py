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

train_test_ratio = 0.1
USE_WHOLE_DATA = True
validationSize = 500
########################################################



# read the data and split it
seqReader = dataRead.SeqReader()
allSeqs = seqReader.readOneHotFromFile('../data/seq.onehot.gz')

if USE_WHOLE_DATA:
	data = allSeqs
else:
	data = [allSeqs[random.randrange(0,len(allSeqs))] for i in range(2000)]

per=np.random.permutation(len(data))
itest=per[:int(len(data)*train_test_ratio)]
itrain=per[int(len(data)*train_test_ratio):]

print "Test set size: " + str(len(itest))
print "Train set size: " + str(len(itrain))

val = [random.randrange(0, len(itrain)) for i in range(validationSize)]

# convert raw sequences to one hot matrices
start = time.time()
trainingData = np.array([data[i] for i in itrain])
testingData = np.array([data[i] for i in itest])
validationData = np.array([data[i] for i in val])

print "Conversion of test set in (in ms): " + str((time.time()-start)*1000)

# construct the model
hyper_params = {'number_of_motifs':30,
				'motif_length':11,
				'learning_rate':0.001,
				'doublestranded':True,
				'pooling_factor':5,
				'epochs':900,
				'cd_k':5,
				'sparsity':0.001, # use 0.0 to disable sparsity constraint
				'rho':0.001,
				'batch_size':100,
				'momentum':0.9 # use 0.0 to disable momentum
}
learner = CRBM(hyperParams=hyper_params)

# add the observers for free energy (test and train)
free_energy_observer = observer.FreeEnergyObserver(learner, testingData, "Free Energy Testing Observer")
learner.addObserver(free_energy_observer)
free_energy_train_observer = observer.FreeEnergyObserver(learner, validationData, "Free Energy Training Observer")
learner.addObserver(free_energy_train_observer)

# add the observers for reconstruction error (test and train)
reconstruction_observer = observer.ReconstructionErrorObserver(learner, testingData, "Reconstruction Error Testing Observer")
learner.addObserver(reconstruction_observer)
reconstruction_observer_train = observer.ReconstructionErrorObserver(learner, validationData, "Reconstruction Error Training Observer")
learner.addObserver(reconstruction_observer_train)

# add the observer of the motifs during training (to look at them afterwards)
param_observer = observer.ParameterObserver(learner, None)
learner.addObserver(param_observer)

# add the motif hit scanner
motif_hit_observer = observer.MotifHitObserver(learner, validationData)
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
plt.title(str(hyper_params["epochs"]) + " epo " + str(hyper_params["motif_length"]) + " kmers " + str(hyper_params["number_of_motifs"]) + " motifs_CD "+str(hyper_params["cd_k"])+".png")
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
