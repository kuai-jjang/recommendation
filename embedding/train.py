# -*- coding: utf-8 -*-

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
    parser.add_argument('--vocab_dir',default="./preprocessing/without_josa_etc", help='vocab?',type=str)
    parser.add_argument('--vocabfreq_dir',default="./preprocessing/my_vocab_frequency", help='vocab?',type=str)
    parser.add_argument('--make_skipgram',default=False, help='make skipgram?',type=bool)
    parser.add_argument('--skipgram_dataset',default='./skip_datasets_witoud_josa.pickle', help='skipgram dataset?',type=str)
    parser.add_argument('--save_dir',default='./w2v_withoud_ns', help='savde directory?',type=str)
    parser.add_argument('--load_dir',default='.', help='load directory?',type=str)
    
    parser.add_argument('--epoch',default=3, help='epoch?',type=int)
    parser.add_argument('--lr',default=0.0001, help='lr?',type=float)
    
    args = parser.parse_args()

    window_size=2

    #사전 불러오기
    with open(args.vocab_dir,'rb') as f: #defaultdict으로 바꿔야됨
        w2i=pickle.load(f)

    #빈도수 사전 불러오기
    with open(args.vocabfreq_dir,'rb') as f: #defaultdict으로 바꿔야됨
        freq_dic=pickle.load(f)


    #skipgram dataset 만들기 -> pickle로 저장해두는게 편할듯?
    if args.make_skipgram:  
        X,y=skipgram('./preprocessing/seq_without_josa_etc.txt',window_size).reading()
        with open('./skip_datasets_witoud_josa.pickle','wb') as f :
            pickle.dump([X,y],f)
    #skipgram dataset 불러오기
    with open(args.skipgram_dataset,'rb') as f :
        skip_gram_set=pickle.load(f)
        X,y=skip_gram_set[0],skip_gram_set[1]


    X=torch.tensor(X).view(-1,1)
    y=torch.tensor(y).view(-1,1) #[0]으로 해줘야 batch 단위로 slicing 가능: ex) tensor([1, 2, 3])


    my_dataset = TensorDataset(X,y) #create your datset
    batchsize=16
    my_dataloader = DataLoader(my_dataset,batch_size=batchsize,shuffle = True,drop_last=True) #create your dataloader

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model=word2vec(vocab_len=len(w2i)+2) #unk이랑 torch.embedding 이 0부터 시작이라는 것을 몰랐다... 
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)

    if len(args.load_dir)>1:
        checkpoint=torch.load(args.load_dir,map_location=device)
        print(checkpoint)
        start_epoch=checkpoint['epoch']+1
        model.load_state_dict(checkpoint['state_dict'])
        model.to(device)
        optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)
        optimizer.load_state_dict(checkpoint['optimizer'])
    else:
        model.to(device)
        start_epoch=0


    criterion=nn.CrossEntropyLoss()
    epochs=start_epoch+args.epoch
    
    for epoch in range(start_epoch,epochs+1):
        running_loss=0.0
        for i,data in enumerate(my_dataloader,0):
            inputs,labels=data
            labels=labels.view(1,-1)[0].to(device)
            inputs=inputs.to(device)

            optimizer.zero_grad()

            outputs=model(inputs).view(batchsize,-1).to(device)
            loss=criterion(outputs,labels)
        
            #loss=negative_sampling(labels,outputs,vocab_len=len(w2i),n=10)
            loss.backward()
            optimizer.step()

            running_loss+=loss.item()
            if i % 499 == 0:    # print every 2000 mini-batches
                print('[%d, %5d] loss: %.5f' %(epoch + 1, i + 1, running_loss / 499))
                running_loss = 0.0


    state={'epoch':epochs,'state_dict':model.state_dict(),'optimizer':optimizer.state_dict()}
    torch.save(state,args.save_dir+'_epoch_'+str(epochs)+'_lr_'+str(args.lr))


