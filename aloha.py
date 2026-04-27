import random as rd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from heapq import heappush, heappop

def duree_exp(p):
    return np.random.exponential(1/p)


def backoff(i,tau):
    """fonction de backoff exponentiel binaire"""
    return np.random.exponential(2**i * tau)


Tmax = 10_000_000


def simulation_aloha(lamda,N=10):
    """simulateur de CSMA/CD"""

    K = 100 #taille de la file d'attente

    t=0
    events = []
    canal_libre = 0
    current_sender=-1

    fin_bouillage = False #nous sers pour ne pas faire plusique fois fin de brouillage
    tranmission_canselled = set()  # Ensemble pour suivre les transmissions annulées
    stations_a_backoff = set()  # Ensemble pour suivre les stations en backoff
    i_par_station = [0] * N  # Initialisation du nombre de points par station à 0
    nb_packets_par_station = [0] * N  # Initialisation du nombre de points par station à 0
    stations_en_attente = set()  # Ensemble pour suivre les stations en attente de transmission

    packets_perdus = 0 #nombre total de paquets perdus
    packets_arrives = 0 #nombre total de paquets arrives vers les machines
    packets_emis = 0 #nombre de paquets emis

    n_t = [] #nombre total de paquet transmis à l'instant t
    clients_t = [] #nombre moyen de paquets en attentes à travers le temps
    perdus_t = [] #nombre de paquet perdu  travers le temps
    last_sender = None

    tau_backoff = 5 #temp d'attente moyen du backoff à l'état 1

    for i in range(N):
        t_arrivee = duree_exp(lamda)
        heappush(events, (t_arrivee, 'arrivee_paquet',i))


    while t<Tmax:
        n_t.append([t,packets_emis])
        clients_t.append([t,sum(nb_packets_par_station)])
        if packets_arrives > 0:
            perdus_t.append([t,packets_perdus/packets_arrives])
        else:
            perdus_t.append([t,0])
        t, event, machine = heappop(events)
        match event:

            case 'debut_transmission':

                if canal_libre == 0:
                    #print('temps de debut de transmission canale libre  :',t,'station :',machine,'current sender :',current_sender)
                    canal_libre = 1
                else:
                    # collision
                    last_sender = machine
                    canal_libre += 1

                heappush(events,(t + 1, 'fin_transmission', machine)) # 10 est le temps de transmission du paquet


            case 'fin_transmission':

                canal_libre -= 1 #le canal redevient libre
                if canal_libre == 0 and machine != last_sender:
                    packets_emis += 1 #increment le nombre de paquets emis "n(t)"
                    nb_packets_par_station[machine] -= 1
                    i_par_station[machine] = 0
                    if nb_packets_par_station[machine] > 0:  # S'il reste des paquets à transmettre pour cette station
                        heappush(events, (t + 0.005, 'debut_transmission', machine)) # on va sense le canal si il est libre ou pas pour le prochain paquet de la station
                else:
                    i_machine = i_par_station[machine]
                    i_par_station[machine]=i_machine+1
                    heappush(events, (t + backoff(i_machine, tau_backoff), 'debut_transmission', machine))
                    if machine == last_sender:
                        last_sender == None





            case 'arrivee_paquet':
                packets_arrives += 1
                nb_packets_par_station[machine]+=1
                heappush(events, (t + duree_exp(lamda), 'arrivee_paquet', machine))

                if nb_packets_par_station[machine] == 1:  # Si la station était vide avant l'arrivée du paquet
                    heappush(events, (t + 0.005, 'debut_transmission', machine)) #si le nombre de  pakets est egale a 1 alors on va snese le canal si il est libre ou pas

                if nb_packets_par_station[machine] == K+1 : #verifie si la file était pleine au moment de l'arrivé du paquet
                    #incrementer le nombre de paquet perdu
                    packets_perdus += 1
                    nb_packets_par_station[machine] = K

    return n_t, clients_t, perdus_t





if __name__ == "__main__":
    #lamda = 0.003
    lamda = 0.05
    N=10
    n_t, clients_t, pertes_t = simulation_aloha(lamda,N)
    x_values, y_values = zip(*n_t)
    debit = [b / a if a != 0 else 0 for a, b in zip(x_values, y_values)]
    #affichage du debit
    plt.figure()
    plt.title("nombre de paquets emis par rapport au temps")
    sns.lineplot(x=x_values, y=debit)
    plt.savefig("debits.pdf")
    plt.close()

    # affichage du nombre de client
    plt.figure()
    plt.title("nombre de paquets en attentre par rapport au temps")
    x_clients, y_clients = zip(*clients_t)
    sns.lineplot(x=x_clients, y=y_clients)
    plt.savefig("clients.pdf")
    plt.close()

    plt.figure()
    plt.title("taux de perte par rapport au temps")
    x_pertes, y_pertes = zip(*pertes_t)
    sns.lineplot(x=x_pertes, y=y_pertes)
    plt.savefig("pertes.pdf")
    plt.close()
