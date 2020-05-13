
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.layers import Embedding
from keras.layers import LSTM
from keras.layers import GRU
from keras.models import model_from_json


def openFile(filename):
    data = pd.read_csv(filename)
    return data



def splitData(dataframe):

    labels=dataframe["MarkerValueInt"].dropna()
    dataframe = dataframe.iloc[labels.index]
    data=dataframe.iloc[:,4:18]
    labels=np.array(labels)
    data=np.array(data)
    # labels = np.reshape(labels, -1, 0)
    return labels,data

def createSlicedData(sliceSize, trainLabels, trainData,testLabels,testData):
    slicedTrainData = []
    slicedTrainLabels = []

    slicedTestData = []
    slicedTestLabels = []
    for i in range(0, len(trainData) - sliceSize):
        data = trainData[i:i + sliceSize]
        datalabels = trainLabels[i:i + sliceSize]
        # no elegant way
        a, TrainLabelsList = np.unique(datalabels, return_counts=True)
        maxValue = np.where(TrainLabelsList == np.amax(TrainLabelsList))[0][0]
        slicedTrainLabels.append(a[maxValue])
        slicedTrainData.append(data)


    for i in range(0, len(testData) - sliceSize):
        data = testData[i:i + sliceSize]
        datalabels = testLabels[i:i + sliceSize]
        # no elegant way
        a, TestLabelsList = np.unique(datalabels, return_counts=True)
        maxValue = np.where(TestLabelsList == np.amax(TestLabelsList))[0][0]
        slicedTestLabels.append(a[maxValue])
        slicedTestData.append(data)

    slicedTrainData = np.asarray(slicedTrainData)
    slicedTrainLabels = np.asarray(slicedTrainLabels)
    slicedTestData = np.asarray(slicedTestData)
    slicedTestLabels = np.asarray(slicedTestLabels)
    return slicedTestData,slicedTestLabels,slicedTrainData,slicedTrainLabels

def biniriazeLabels(slicedTrainLabels,slicedTestLabels) :
    # One-Hot encdoing for labels

    Trainlb = preprocessing.LabelBinarizer()
    Trainlb.fit(slicedTrainLabels)
    slicedTrainLabels = Trainlb.transform(slicedTrainLabels)

    Testlb = preprocessing.LabelBinarizer()
    Testlb.fit(slicedTestLabels)
    slicedTestLabels = Testlb.transform(slicedTestLabels)
    return slicedTrainLabels, slicedTestLabels, Testlb

def buildModel(sliceSize,slicedTrainData,slicedTrainLabels):
    # code for building an LSTM with 100 neurons
    model = Sequential()
    model.add(LSTM(100, return_sequences=False, input_shape=(sliceSize, len(slicedTrainData[0][0]))))
    model.add(Dropout(0.5))
    model.add(Dense(3, activation='sigmoid'))

    model.compile(loss='binary_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])

    model.fit(slicedTrainData, slicedTrainLabels, batch_size=64, epochs=50)
    return model

def saveModel(model):
    # serialize model to JSON
    model_json = model.to_json()
    with open("./test/model.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights("./test/model.h5")
    print("Saved model to disk")

dfTrain=openFile('D:/FinalProject/test/t_30.04.20_18.03.53.csv')
dfTest=openFile('D:/FinalProject/test/t_30.04.20_18.03.53.csv')
trainLabels,trainData=splitData(dfTrain)
testLabels,testData=splitData(dfTest)
sliceSize=127

slicedTestData, slicedTestLabels, slicedTrainData, slicedTrainLabels = createSlicedData(sliceSize,trainLabels,trainData,
                                                                                      testLabels,testData)


slicedTrainLabels, slicedTestLabels ,Testlb= biniriazeLabels(slicedTrainLabels,slicedTestLabels)

model = buildModel(sliceSize,slicedTrainData,slicedTrainLabels)

saveModel(model)
score = model.evaluate(slicedTestData, slicedTestLabels, batch_size=64)
print("Accuracy: %.2f%%" % (score[1]*100))
prediction=model.predict(slicedTestData, batch_size=64)

result=[]
for i in range (0,len(prediction)):
    maxIndex=np.argmax(prediction[i])
    result.append(maxIndex+1)



print(prediction)
print(result)

slicedTestLabels = Testlb.inverse_transform(slicedTestLabels)
print(slicedTestLabels)
'''
# print(slicedTestLabels[[1487]])
countSuccessDict= {1:0,2:0,0:0}
countFailedDict= {1:0,2:0,0:0}
count = 0
count2 = 0
for i in range(0, len(result)):
    if result[i] != slicedTestLabels[i]:
        count = count + 1
        countFailedDict[slicedTestLabels[i]] = countFailedDict[slicedTestLabels[i]] + 1
    if result[i] == slicedTestLabels[i]:
        count2 = count2 + 1
        countSuccessDict[slicedTestLabels[i]] = countSuccessDict[slicedTestLabels[i]] + 1

print("done")
# count3= np.count_nonzero(TrainLabels==0)
# count4= np.count_nonzero(TestLabels==0)
# count5= np.count_nonzero(result==0)
print(count, "samples failed")
print(count2, "samples succeeded")
sum = count + count2
print("overall succeess rate", (count2/sum)*100, "%")
# print(\"How many 0 where predicted\",count5,\"how many actual 0 there are\",count4)\n",
# print(\"unknown rate train\", (count3/sum)*100,\"%\")\n",
# print(\"unknown rate test\", (count4/sum)*100,\"%\")\n",
# print(\"predicting event #0 success rate\",countSuccessDict[0]/(countSuccessDict[0]+countFailedDict[0])*100,\"% fail rate\",countFailedDict[0]/(countSuccessDict[0]+countFailedDict[0])*100,\"%\")
print("predicting event #1 success rate",countSuccessDict[1]/(countSuccessDict[1]+countFailedDict[1])*100,"% fail rate",countFailedDict[1]/(countSuccessDict[1]+countFailedDict[1])*100,"%")
print("predicting event #2 success rate",countSuccessDict[2]/(countSuccessDict[2]+countFailedDict[2])*100,"% fail rate",countFailedDict[2]/(countSuccessDict[2]+countFailedDict[2])*100,"%")
print("predicting event #0 success rate",countSuccessDict[0]/(countSuccessDict[0]+countFailedDict[0])*100,"% fail rate",countFailedDict[0]/(countSuccessDict[0]+countFailedDict[0])*100,"%")
'''


