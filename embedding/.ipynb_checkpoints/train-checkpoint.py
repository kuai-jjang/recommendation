from w2vec import word2vec,negative_sampling
import torch
import torch.nn as nn
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader,TensorDataset
import torch.optim as optim

import numpy as np
import argparse
import pickle

##TODO

### sequence 저장 형식 바꾸기

class skipgram:
    def __init__(self,finename,window_size=2):

        self.filename=finename
        self.window=window_size
        self.x_input=[]
        self.target=[]

    def reading(self):
        with open(self.filename, 'r') as f:
            lines = f.readlines()
            step=0
            for line in lines:
                step+=1
                if step%1000==0:
                    print(step)
                if len(line)>self.window+2:
                    line=list(map(lambda x:int(x),line.replace(' \n','').split(' ')))   #다음부터는 pickle로 저장하자.
                    self.slicing(line)

        return self.x_input,self.target


    def slicing(self,line):
        for i in range(self.window,len(line)-self.window):
            self.x_input.append(line[i-self.window:i]+line[i+1:i+1+self.window])
            self.target.append([line[i] for k in range(self.window*2)])



if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--vocab_dir',default="./preprocessing/my_vocab_freq_3.pickle", help='vocab?',type=str)
    parser.add_argument('--make_skipgram',default=False, help='make skipgram?',type=str)
    parser.add_argument('--skipgram_dataset',default='./skip_datasets.pickle', help='skipgram dataset?',type=str)
    
    args = parser.parse_args()

    window_size=2

    #사전 불러오기
    with open(args.vocab_dir,'rb') as f: #defaultdict으로 바꿔야됨
        w2i=pickle.load(f)

    #skipgram dataset 만들기 -> pickle로 저장해두는게 편할듯?

    if args.make_skipgram:  
        X,y=skipgram('./preprocessing/sentence4idx.txt',window_size).reading()
        with open('./skip_datasets.pickle','wb') as f :
            pickle.dump([X,y],f)

    with open(args.skipgram_dataset,'rb') as f :
        skip_gram_set=pickle.load(f)
        X,y=skip_gram_set[0],skip_gram_set[1]


    X=torch.tensor(X).view(-1,1)
    y=torch.tensor(y).view(-1,1) #[0]으로 해줘야 batch 단위로 slicing 가능: ex) tensor([1, 2, 3])


    my_dataset = TensorDataset(X,y) # create your datset
    batchsize=16
    my_dataloader = DataLoader(my_dataset,batch_size=batchsize) # create your dataloader
    
    model=word2vec(vocab_len=len(w2i)+2) #unk이랑 torch.embedding 이 0부터 시작이라는 것을 몰랐다... 
    print(len(w2i))
    

    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    #criterion = negative_sampling()
    criterion=nn.CrossEntropyLoss()


    # print(iter(my_dataloader).next())
    
    epochs=1
    
    for epoch in range(epochs):
        running_loss=0.0
        for i,data in enumerate(my_dataloader,0):
            inputs,labels=data
            labels=labels.view(1,-1)[0]

            optimizer.zero_grad()

            outputs=model(inputs).view(batchsize,-1)
            loss=criterion(outputs,labels)
        
            #loss=negative_sampling(labels,outputs,vocab_len=len(w2i),n=10)
            loss.backward()
            optimizer.step()

            running_loss+=loss.item()
            if i % 49 == 0:    # print every 2000 mini-batches
                print('[%d, %5d] loss: %.5f' %(epoch + 1, i + 1, running_loss / 50))
                running_loss = 0.0

