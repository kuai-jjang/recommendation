import torch
import torch.nn as nn


class doc2vec(nn.Module):

    def __init__(self,model, freq_dic,lecture_len, lecture_dim=256, ns=5):
        super(doc2vec, self).__init__()
        
        self.lecture_len=lecture_len
        self.lecuter_dim=lecture_dim
        self.lecture = nn.Embedding(lecture_len,lecture_dim)
        self.word_emb=model['embedding_in.weight'].detach()
        self.n=ns
        self.freq_dic=torch.tensor(freq_dic)


    def forward(self, inputs, target):

        batch_size = target.size()[0]
 

        doc_id=torch.LongTensor(inputs[:,0].unsqueeze(1))
        context=inputs[:,1:]

        lec_vec=self.lecture(doc_id)
        context_vec=self.word_emb[context]
        target_vec=self.word_emb[target].unsqueeze(1)

        nwords=torch.multinomial(self.freq_dic,batch_size*self.n).view(batch_size,self.n)  
        n_vec=self.word_emb[nwords].neg().view(batch_size,-1,self.n)

        d_vec=torch.cat((lec_vec,context_vec),1).mean(1).unsqueeze(1)
        
        return d_vec,target_vec,n_vec
        # i_loss=torch.bmm(d_vec,target_vec.permute(0,2,1))

        # return i_loss.mean()



def negative_sampling(d_vec,target_vec,n_vec):

    batch_size=target_vec.shape[0]
    o_loss=torch.bmm(d_vec,target_vec.view(batch_size,-1,1)).sigmoid().log().mean().neg()
    n_loss=torch.bmm(d_vec,n_vec).sigmoid().log().mean().neg()
    loss=o_loss+n_loss

    return loss.mean()  #batch니까 mean