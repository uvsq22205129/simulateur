import random as rd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from heapq import heappush, heappop

def duree_exp(p):
    return np.random.exponential(1/p)


def backoff(i,tau):
    """fonction de backoff exponentiel binaire"""
    return np.random.exponential(1/(2**i * tau))


Tmax = 1000


def simulation_csmacd(lamda,N=10):
    """simulateur de CSMA/CD"""

    K = 10 #taille de la file d'attente

    t=0
    events = []
    canal_libre = True
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


    tau_backoff = 0.1 #temp d'attente moyen du backoff à l'état 1

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

            case 'sense':
                if canal_libre:
                    heappush(events, (t + 0.5, 'debut_transmission', machine)) # si le canal est libre on commance a transmettre le paquet 0.05 est le temps pour commencer a transmettre le paquet
                else:
                    stations_en_attente.add(machine)



            case 'debut_transmission':

                if canal_libre:
                    #print('temps de debut de transmission canale libre  :',t,'station :',machine,'current sender :',current_sender)

                    canal_libre = False
                    current_sender = machine
                    heappush(events,(t + 10, 'fin_transmission', machine)) # 10 est le temps de transmission du paquet

                else:
                    # collision


                    machine1=current_sender
                    machine2=machine

                    tranmission_canselled.add(machine1)  # Ajouter la machine actuelle à l'ensemble des transmissions annulées



                    #print('collision current_sender:',current_sender,'temps :',t)
                    # print('tranission cansaled:')
                    # print(tranmission_canselled)


                    if current_sender not in stations_a_backoff:  # Si la machine actuelle n'est pas déjà en backoff
                        i_machine1=i_par_station[machine1]
                        i_par_station[machine1]=i_machine1 + 1
                        stations_a_backoff.add(machine1)  # Ajouter la machine actuelle à l'ensemble des stations en backoff
                        heappush(events, (t + backoff(i_machine1, tau_backoff), 'sense', machine1))


                    i_machine2=i_par_station[machine2]
                    i_par_station[machine2]=i_machine2+1
                    stations_a_backoff.add(machine2)  # Ajouter la machine qui arrive à l'ensemble des stations en backoff



                    if machine2 in stations_en_attente:
                        stations_en_attente.remove(machine2)  # retirer cette machine si elle est impliquee dans une collision car son sense est gere par le backoff


                    heappush(events, (t + backoff(i_machine2, tau_backoff), 'sense', machine2))

                    if(not fin_bouillage):
                        fin_bouillage = True  # Indiquer que le bouillage est en cours
                        heappush(events, (t + 1, 'fin_bouillage', None)) # brouillage pendant 1 s


            case 'fin_bouillage':
                #print('fin de bouillage :',t)
                fin_bouillage = False  # Réinitialiser le flag de fin de bouillage
                canal_libre = True #le canal redevient libre après le bouillage
                current_sender = -1 #il n y a plus de machine qui transmet
                for station in stations_en_attente:
                    heappush(events, (t + 0.005, 'sense', station)) # on va snese le canal pour les autres stations qui sont en attente de transmission

                stations_en_attente.clear()  # Vider l'ensemble des stations en attente après le bouillage

            case 'fin_transmission':

                if machine not in tranmission_canselled:  # Vérifier si la machine n'est pas dans l'ensemble des transmissions annulées
                    #print('*** temps de fin de transmission canale libre  :',t,'station :',machine,'current sender :',current_sender)

                    current_sender = -1 #il n y a plus de machine qui transmet
                    canal_libre = True #le canal redevient libre
                    packets_emis += 1 #increment le nombre de paquets emis "n(t)"

                    nb_packets_par_station[machine] -= 1
                    if nb_packets_par_station[machine] > 0:  # S'il reste des paquets à transmettre pour cette station
                        heappush(events, (t + 0.005, 'sense', machine)) # on va sense le canal si il est libre ou pas pour le prochain paquet de la station

                    if machine in stations_en_attente:
                        stations_en_attente.remove(machine)  # Retirer la station de l'ensemble des stations en attente

                    for station in stations_en_attente:
                        heappush(events, (t + 0.005, 'sense', station)) # on va snese le canal pour les autres stations qui sont en attente de transmission
                    stations_en_attente.clear()  # Vider l'ensemble des stations en attente après la fin de la transmission

                    if machine in stations_a_backoff:
                        stations_a_backoff.remove(machine)  # Retirer la station de l'ensemble des stations en backoff

                    i_par_station[machine] = 0  # Réinitialiser le compteur de backoff pour la station qui a réussi à transmettre
                else:
                    tranmission_canselled.discard(machine)




            case 'arrivee_paquet':
                packets_arrives += 1
                nb_packets_par_station[machine]+=1
                heappush(events, (t + duree_exp(lamda), 'arrivee_paquet', machine))

                if nb_packets_par_station[machine] == 1:  # Si la station était vide avant l'arrivée du paquet
                    heappush(events, (t + 0.005, 'sense', machine)) #si le nombre de  pakets est egale a 1 alors on va snese le canal si il est libre ou pas

                if nb_packets_par_station[machine] == K+1 : #verifie si la file était pleine au moment de l'arrivé du paquet
                    #incrementer le nombre de paquet perdu
                    packets_perdus += 1
                    nb_packets_par_station[machine] = K

    return n_t, clients_t, perdus_t





if __name__ == "__main__":
    #lamda = 0.003
    lamda = 0.1
    N=100
    n_t, clients_t, pertes_t = simulation_csmacd(lamda,N)
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
