from cgi import test
import os, sys
import pathlib as path
import glob
import zipfile
import h5py
import numpy as np
import matplotlib.pyplot as plt
from pyparsing import Word
import torch
from torch.utils.data import Dataset, DataLoader

# import slayer from lava-dl
import lava.lib.dl.slayer as slayer

import IPython.display as display
from matplotlib import animation


import nni


class Network(torch.nn.Module):
    def __init__(self):
        super(Network, self).__init__()

        neuron_params = {
                'threshold'     : 1.25,
                'current_decay' : 0.25,
                'voltage_decay' : 0.03,
                'tau_grad'      : 0.03,
                'scale_grad'    : 3,
                'requires_grad' : True,     
            }
        neuron_params_drop = {**neuron_params, 'dropout' : slayer.neuron.Dropout(p=0.05),}
        
        self.blocks = torch.nn.ModuleList([
                slayer.block.cuba.Dense(neuron_params_drop, 34*34*2, 512, weight_norm=True, delay=True),
                slayer.block.cuba.Dense(neuron_params_drop, 512, 512, weight_norm=True, delay=True),
                slayer.block.cuba.Dense(neuron_params, 512, 10, weight_norm=True),
            ])
    
    def forward(self, spike):
        for block in self.blocks:
            spike = block(spike)
        return spike
    
    def grad_flow(self, path):
        # helps monitor the gradient flow
        grad = [b.synapse.grad_norm for b in self.blocks if hasattr(b, 'synapse')]

        plt.figure()
        plt.semilogy(grad)
        plt.savefig(path + 'gradFlow.png')
        plt.close()

        return grad

    def export_hdf5(self, filename):
        # network export to hdf5 format
        h = h5py.File(filename, 'w')
        layer = h.create_group('layer')
        for i, b in enumerate(self.blocks):
            b.export_hdf5(layer.create_group(f'{i}'))


def main(args, trained_folder,net_tmp_name):

    os.makedirs(trained_folder, exist_ok=True)

    # device = torch.device('cpu')
    device = torch.device('cuda') 

    net = Network().to(device)

    optimizer = torch.optim.Adam(net.parameters(), lr=args['lr'])

    if args['error'] == "spike_max":
        error = slayer.loss.SpikeMax().to(device)
        stats = slayer.utils.LearningStats()
        assistant = slayer.utils.Assistant(net, error, optimizer, stats, classifier=slayer.classifier.Rate.predict)

    if args['error'] == "spike_rate":
        error = slayer.loss.SpikeRate(true_rate=0.2, false_rate=0.03, reduction='sum').to(device)
        stats = slayer.utils.LearningStats()
        assistant = slayer.utils.Assistant(net, error, optimizer, stats, classifier=slayer.classifier.Rate.predict)

    if args['error'] == "spike_time":
        error = slayer.loss.SpikeTime().to(device)
        stats = slayer.utils.LearningStats()
        assistant = slayer.utils.Assistant(net, error, optimizer, stats, classifier=slayer.classifier.MovingWindow(time_window=1).predict)



    epochs = args['epochs']

    for epoch in range(epochs):
        for i, (input, label) in enumerate(train_loader): # training loop
            output = assistant.train(input, label)
        print(f'\r[Epoch {epoch:2d}/{epochs}] {stats}', end='')
            
        for i, (input, label) in enumerate(test_loader): # training loop
            output = assistant.test(input, label)
        print(f'\r[Epoch {epoch:2d}/{epochs}] {stats}', end='')
            
        if epoch%20 == 19: # cleanup display
            print('\r', ' '*len(f'\r[Epoch {epoch:2d}/{epochs}] {stats}'))
            stats_str = str(stats).replace("| ", "\n")
            print(f'[Epoch {epoch:2d}/{epochs}]\n{stats_str}')
        
        if stats.training.best_accuracy:
            torch.save(net.state_dict(), trained_folder + net_tmp_name +'_train.pt')

        if stats.testing.best_accuracy:
            torch.save(net.state_dict(), trained_folder + net_tmp_name +'.pt')

        stats.update()
        stats.save(trained_folder + '/')
        net.grad_flow(trained_folder + '/')
        
        print(stats.testing.accuracy_log[-1]*100) 
        nni.report_intermediate_result(stats.testing.accuracy_log[-1]*100)
    
    print(stats.testing.max_accuracy*100)
    nni.report_final_result(stats.testing.max_accuracy*100)
    
    
    return stats.training.max_accuracy, stats.testing.max_accuracy