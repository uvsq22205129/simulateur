import random as rd
import seaborn as sns
import numpy as np
from heapq import heappush, heappop

def duree_exp(p):
    return np.random.exponential(1/p)


def backoff(i,tau):
    """fonction de backoff exponentiel binaire"""
    return np.random.exponential(1/(2**i * tau))
    

Tmax = 1000


def simulation_csmacd(lamda,N=10):
    """simulateur de CSMA/CD"""


    t=0
    events = []
    canal_libre = True
    current_sender=-1
    
    tranmission_canselled = -1
    stations_a_backpff = set()  # Ensemble pour suivre les stations en backoff
    i_par_station = [2] * N  # Initialisation du nombre de points par station à 0
    nb_packets_par_station = [0] * N  # Initialisation du nombre de points par station à 0
    stations_en_attente = set()  # Ensemble pour suivre les stations en attente de transmission

    for i in range(N):
        t_arrivee = duree_exp(lamda)
        heappush(events, (t_arrivee, 'arrivee_paquet',i))


    while t<Tmax:

        t, event,machine = heappop(events)
        print('temps:',t)
        match event:

            case 'sense':
                if canal_libre:
                    heappush(events, (t + 0.05, 'debut_transmission', machine)) # si le canal est libre on commance a transmettre le paquet 0.05 est le temps pour commencer a transmettre le paquet 
                else:
                    stations_en_attente.add(machine)



            case 'debut_transmission':
                if canal_libre:
                    canal_libre = False
                    current_sender = machine
                    heappush(events,(t + 0.8, 'fin_transmission', machine)) # 0.8 est le temps de transmission du paquet
                else:
                    # collision 
                    print('collision')
                    machine1=current_sender
                    machine2=machine

                    tranmission_canselled = current_sender

                    if current_sender not in stations_a_backpff:  # Si la machine actuelle n'est pas déjà en backoff
                        i_machine1=i_par_station[machine1] 
                        i_par_station[machine1]=i_machine1 + 1
                        stations_a_backpff.add(machine1)  # Ajouter la machine actuelle à l'ensemble des stations en backoff
                        heappush(events, (t + backoff(i_machine1, 0.1), 'sense', machine1))


                    i_machine2=i_par_station[machine2]
                    i_par_station[machine2]=i_machine2+1
                    stations_a_backpff.add(machine2)  # Ajouter la machine qui arrive à l'ensemble des stations en backoff



                    if machine2 in stations_en_attente:
                        stations_en_attente.remove(machine2)  # retirer cette machine si elle est impliquee dans une collision car son sense est gere par le backoff


                    heappush(events, (t + backoff(i_machine2, 0.1), 'sense', machine2)) 

                    heappush(events, (t + 1, 'fin_bouillage', None)) # brouillage pendant 1 s 


            case 'fin_bouillage':
                canal_libre = True #le canal redevient libre après le bouillage
                current_sender = -1 #il n y a plus de machine qui transmet
                for station in stations_en_attente:
                    heappush(events, (t + 0.005, 'sense', station)) # on va snese le canal pour les autres stations qui sont en attente de transmission

                stations_en_attente.clear()  # Vider l'ensemble des stations en attente après le bouillage

            case 'fin_transmission':
                if tranmission_canselled != machine:
                    current_sender = -1 #il n y a plus de machine qui transmet
                    canal_libre = True #le canal redevient libre 


                    nb_packets_par_station[machine] -= 1
                    if nb_packets_par_station[machine] > 0:  # S'il reste des paquets à transmettre pour cette station
                        heappush(events, (t + 0.005, 'sense', machine)) # on va snese le canal si il est libre ou pas pour le prochain paquet de la station

                    if machine in stations_en_attente:
                        stations_en_attente.remove(machine)  # Retirer la station de l'ensemble des stations en attente
                
                    for station in stations_en_attente:
                        heappush(events, (t + 0.005, 'sense', station)) # on va snese le canal pour les autres stations qui sont en attente de transmission
                    stations_en_attente.clear()  # Vider l'ensemble des stations en attente après la fin de la transmission

                    if machine in stations_a_backpff:
                        stations_a_backpff.remove(machine)  # Retirer la station de l'ensemble des stations en backoff
                    
                    i_par_station[machine] = 2  # Réinitialiser le compteur de backoff pour la station qui a réussi à transmettre
                else:
                    tranmission_canselled = -1




            case 'arrivee_paquet':
                nb_packets_par_station[machine]+=1
                heappush(events, (t + duree_exp(lamda), 'arrivee_paquet', machine))

                if nb_packets_par_station[machine] == 1:  # Si la station était vide avant l'arrivée du paquet
                    heappush(events, (t + 0.005, 'sense', machine)) #si le nombre de  pakets est egale a 1 alors on va snese le canal si il est libre ou pas        
                




if __name__ == "__main__":
    lamda = 0.003
    N=100
    simulation_csmacd(lamda,N)