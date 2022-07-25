
import os
import torchvision.datasets as datasets
from torchvision import transforms
import matplotlib.pyplot as plt
import nni
import numpy as np
import lava.lib.dl.slayer as slayer
from matplotlib import animation
import IPython.display as display

##custom transformation to encode images in spikes
class To_spikes(object):
    def __init__(self,time_steps, vth, img_H, img_W=None): ##return a np.array of (HxW,timesteps)
        if img_W==None:
            img_W=img_H
        self.shape = img_H*img_W
        self.vth =vth
        self.time_steps = time_steps

        self.v=np.zeros((self.shape,))

    def __call__(self, sample):
        
        out =[]
        sample = np.array(sample,dtype=np.int32)
        #sample = sample -127
        sample = (sample/255 -0.5)*2
        #scalare tra -1 e 1 l'immagine
        sample = np.reshape(sample, (self.shape,))
        for i in range(self.time_steps):
           
            self.v = self.v + sample
            tmp = self.v > self.vth
            self.v[tmp] = 0

            if i==0:
                out=np.array([tmp])
            else:
                out=np.vstack((out,tmp))
        
        self.v[:] = 0
        
        return out.T.astype(np.float32)

class squeeze_Tensor(object):
    
    def __init__(self, dim):
        self.dim = dim

    def __call__(self, sample):
        return sample.squeeze(self.dim)

if __name__ == "__main__":
    
    #vth = 22
    '''
    x = np.arange(start=0, stop=256, step=1)
    y = (x/255 -0.5)*2
    plt.figure()
    plt.plot(x,y)
    plt.show()
    '''
    
    os.chdir('./dataset_encoding/')
    os.mkdir('gifs/')

    for vth in np.arange(start=0, stop=5, step=0.5):
        os.mkdir(f'gifs/{vth}')
        transformation = transforms.Compose([To_spikes(128, vth, 28),transforms.ToTensor(),squeeze_Tensor(0)])
        testing_set  = datasets.MNIST(root='./data', train=False, download=True, transform=transformation)
        
        for i in range(5):
            spike_tensor, label = testing_set[np.random.randint(len(testing_set))]
            print(f'spike tensor shape:{spike_tensor.size()}')
            out_np = spike_tensor.cpu().data.numpy().reshape(1, 784, -1)
            out_event = slayer.io.tensor_to_event(out_np)
            print(f'out_shape:{out_np.shape}')
            event_np =spike_tensor.cpu().data.numpy().reshape(1, 28, 28, -1)
            event = slayer.io.tensor_to_event(event_np)
            print(f'event shape: {event_np.shape}')
            anim = event.anim(plt.figure(figsize=(5, 5)), frame_rate=240)
            out_anim = out_event.anim(plt.figure(figsize=(20, 10)), frame_rate=240)
            anim.save(f'gifs/{vth}/gif{i}_l{label}_vth{vth}.gif', animation.PillowWriter(fps=24), dpi=300)
            out_anim.save(f'gifs/{vth}/spike{i}_l{label}_vth{vth}.gif', animation.PillowWriter(fps=24), dpi=300)

    '''    gif_td = lambda gif: f'<td> <img src="{gif}" alt="Drawing" style="height: 250px;"/> </td>'
    html = '<table>'
    html += '<tr><td align="center"><b>Input</b></td><td><b>Output</b></td></tr>'
    for i in range(5):
        html += '<tr>'
        html += gif_td(f'./gifs/gif{i}*')
        html += gif_td(f'./gifs/spike{i}*')
        html += '</tr>'
    html += '</tr></table>'
    display.HTML(html)
    '''


'''
    #vett, label = testing_set.__getitem__(8)
    plt.figure()
    plt.title(label=label)
    "salvare metodo di show output dataset"
    plt.scatter(np.where(vett != 0)[1],np.where(vett != 0)[0], s=2)
    plt.show()
'''

''' 
    timestep= range(128)
    y = []
    cp = np.copy(vett)
    x_timestamp=[]
    y_addr=[]
   [784,128]
    for j in range(128):
        for i in range(784):
            if cp[i][j]!=0: 
                cp[i][j]=i
                x_timestamp.append(j)
                y_addr.append(i)
            else:
                cp[i][j]=0
    
    
    plt.plot(x_timestamp, y_addr, '.', markersize=1)
    plt.show()
'''        



'''nni per giocare con la soglia, passaggi della lista
statistica sull output dell primo step di encoding

- NNI su struttura della rete
- NNI per pruning
- aumentare il più possibile l'accuracy
- NNI su encoding per monitorare l'attività dei neuroni
'''
