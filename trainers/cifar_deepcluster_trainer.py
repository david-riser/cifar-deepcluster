import numpy as np
import os

from base.base_trainer import BaseTrain
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import adjusted_rand_score

class CifarDeepClusterTrainer(BaseTrain):

    def __init__(self, model, data, config):
        super(CifarDeepClusterTrainer, self).__init__(model, data, config)

    def init_callbacks(self):
        pass
        
    def clustering_target_distribution(self, q):
        weight = q ** 2 / q.sum(0)
        return (weight.T / weight.sum(1)).T
        
    def train(self):

        #self.init_clusters_()        

        self.loss = []
        self.ar_score = []
        print("[INFO] Starting the training.")

        # Train for some epochs and always do the kmeans first.
        for epoch in range(self.config.trainer.epochs):

            # Perform kmeans to label our dataset
            # for this round of training.
            self.init_clusters_()

            batch_loss = []
            batch_ar_score = []
            for batch in range(self.config.trainer.batches_per_epoch):
                x_batch, y_true = next(self.data.get_train_flow())
                y_batch = self.kmeans.predict(self.model.backbone.predict(x_batch))
                batch_loss.append(self.model.model.train_on_batch(x_batch, y_batch))
                batch_ar_score.append(adjusted_rand_score(
                    y_true.reshape(-1,), np.argmax(
                        self.model.model.predict(x_batch), axis=1)
                ))
                
                print("[INFO] Epoch {0}, Batch {1}, Batch Loss {2:6.4f}, Batch ARI {3:6.4f}".format(
                    epoch, batch, batch_loss[-1], batch_ar_score[-1]
                ))
                
            print("[INFO] Epoch {0}, Loss {1:6.3f} +/- {2:6.3f}".format(
                epoch, np.mean(batch_loss), np.std(batch_loss)
            ))
            print("[INFO] Epoch {0}, ARI {1:6.3f} +/- {2:6.3f}".format(
                epoch, np.mean(batch_ar_score), np.std(batch_ar_score)
            ))
                
            self.loss.append(np.mean(batch_loss))
            self.ar_score.append(np.mean(batch_ar_score))

        #update_interval = int(np.ceil(self.config.trainer.batches / self.config.trainer.target_updates))
        #if update_interval == 0:
        #    update_interval = 1        
        #print("[INFO] Using update interval {}".format(update_interval))
    
        #kld_loss = []
        #ar_score = []
        #loss = np.inf
        #for iteration in range(self.config.trainer.batches):

            #if iteration % update_interval == 0:
            # 
            #    (x_batch, y_batch) = next(self.data.get_train_flow())
            #    while len(x_batch) != self.config.data_loader.batch_size:
            #        (x_batch, y_batch) = next(self.data.get_train_flow())            

                #q = self.model.model.predict(x_batch, verbose=0)
                #p = self.clustering_target_distribution(q)


            #(x_batch, y_batch) = next(self.data.get_train_flow())
            #if len(x_batch) == self.config.data_loader.batch_size:
            #    loss = self.model.model.train_on_batch(x=x_batch, y=p)
            #    kld_loss.append(loss)
            #    ar_score.append(adjusted_rand_score(
            #        y_batch.reshape(-1,),
            #        np.argmax(self.model.model.predict(x_batch), axis=1)
            #    ))
                
            #print("[INFO] Epoch: {0}, Loss: {1:8.4f}, AR Score {2:8.4f}".format(
            #    iteration, loss, ar_score[-1]))
            
        #self.loss = kld_loss
        #self.rand_index = ar_score


    def init_clusters_(self):

        print("[INFO] Initializing cluster centroids w/ Kmeans (mini-batch).")
        if self.config.data_loader.batch_size < self.config.model.n_clusters:
            print("[FATAL] Mini-batch KMeans requires a batch size at least as large as the number of clusters.")
            exit()

        self.kmeans = MiniBatchKMeans(n_clusters=self.config.model.n_clusters,
                                      init='k-means++', reassignment_ratio=0.04)

        for epoch in range(self.config.trainer.kmeans_epochs):
            for batch in range(self.config.trainer.kmeans_batches_per_epoch):
                (x_batch, y_batch) = next(self.data.get_train_flow())
                self.kmeans.partial_fit(
                    self.model.backbone.predict(x_batch)
                )

        #self.model.model.get_layer("clustering_layer").set_weights(
        #    [self.kmeans.cluster_centers_]
        #)

        
