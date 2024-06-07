import threading
import queue
import time
import random
from matplotlib import pyplot as plt
import numpy as np

# Constants
MAX_QUEUE_SIZE = 3
NUM_TELLERS = 3
TIME_QUANTUM = 2

# Global variables
customer_queue = queue.Queue()
customer_queue_sjf=queue.PriorityQueue()
customer_queue_lock = threading.Lock()
total_waiting_time = 0
total_turnaround_time = 0
total_response_time = 0
total_customers = 0
stop_simulation = threading.Event()
stop_arrival = threading.Event()
avg_times=[]
teller_service_data = {1: [], 2: [], 3: []}  # To store service times for each teller
customers_served_by_teller = {1: [], 2: [], 3: []}  # To store customers each teller served

class Customer:
    def __init__(self, id, arrival_time, burst_time):
        self.id = id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.start_service_time = 0
        self.completion_time = 0

# Function to generate random burst time
def generate_random_burst_time():
    return random.randint(1,10)

def stop_simulation_on_keypress():
    input("Press Enter to stop the simulation...\n")
    stop_arrival.set()

def customer_arrival(queue_type):
    global total_customers
    customer_id = 1
    while not stop_arrival.is_set():
        if not queue_type.full():
            arrival_time = time.time()
            burst_time = generate_random_burst_time()
            customer = Customer(customer_id, arrival_time, burst_time)
            if queue_type == customer_queue:
                queue_type.put(customer)
            else:
                queue_type.put((burst_time, customer.id, customer))

            print(f"Customer {customer_id} enters the Queue with burst time {burst_time}")
            customer_id += 1
            total_customers += 1
        else:
            print("Queue is FULL.")
        time.sleep(1)

def calculate_total_time(customer):
    global total_waiting_time, total_turnaround_time, total_response_time

    turnaround_time = customer.completion_time - customer.arrival_time
    waiting_time = turnaround_time-customer.burst_time
    response_time = customer.start_service_time - customer.arrival_time

    print(f" Customer: {customer.id} Turn around time:{turnaround_time} , Waiting time:{waiting_time} , Response time:{response_time}")

    total_turnaround_time += turnaround_time
    total_waiting_time += waiting_time
    total_response_time += response_time

def calculate_average_time():
    avg_waiting_time = total_waiting_time / total_customers
    avg_turnaround_time = total_turnaround_time / total_customers
    avg_response_time = total_response_time / total_customers

    print(f"Average Waiting Time: {avg_waiting_time:.2f}")
    print(f"Average Turnaround Time: {avg_turnaround_time:.2f}")
    print(f"Average Response Time: {avg_response_time:.2f}")

    return [avg_waiting_time, avg_turnaround_time, avg_response_time]

def plot_average_time_and_teller_service_data(avg_times):
    X = np.array(["AWT", "ATAT", "ART"])
    Y=np.array(avg_times)
    width = 0.35

    labels=['Teller 1', 'Teller 2', 'Teller 3']
    colors = ['r', 'g', 'b']

    plt.figure(figsize=(7, 9))

    # Bar plot for average times
    plt.subplot(2, 1, 1)
    for i in range(len(X)):
        plt.bar(X[i], Y[i], width, color=colors[i], label=X[i])
    plt.title('Average Times', fontsize=18)
    plt.legend()

    # Line plot for teller service data
    plt.subplot(2, 1, 2)
    for (id,_),(color,label) in zip (teller_service_data.items(),zip(colors,labels)):
        label_once = True
        for service in teller_service_data[id]:
            customer_id, start_time, end_time = service
            plt.plot([start_time, end_time], [id, id], color=color, marker='o', label=label if label_once else '')
            label_once=False
            mid_time = (start_time + end_time) / 2
            plt.text(mid_time, id, f"{customer_id}", ha='center', va='bottom')
    
    plt.xlabel('Time (s)')
    plt.ylabel('Teller ID')
    plt.title('Teller Service Times')
    plt.yticks([1, 2, 3], ['Teller 1', 'Teller 2', 'Teller 3'])
    plt.ylim(0.5, 3.5)
    plt.legend()
    plt.grid(True)
    plt.show()





def teller_fcfs(id):
    while not stop_simulation.is_set() or not customer_queue.empty():
        if not customer_queue.empty():
            with customer_queue_lock:
                customer = customer_queue.get()

            customer.start_service_time=time.time()
            print(f"Customer {customer.id} is in Teller {id}")

            teller_service_data[id].append((customer.id,customer.start_service_time,customer.start_service_time+customer.burst_time))
            customers_served_by_teller[id].append(customer.id)

            time.sleep(customer.burst_time)
            customer.completion_time = time.time()
            print(f"Customer {customer.id} leaves Teller {id} ")

            calculate_total_time(customer)

 
def teller_rr(id):
    while not stop_simulation.is_set() or not customer_queue.empty():
        if not customer_queue.empty():
            with customer_queue_lock:
                customer = customer_queue.get()

            if customer.start_service_time == 0:
                customer.start_service_time = time.time()

            if customer.burst_time > TIME_QUANTUM:
                customer.burst_time -= TIME_QUANTUM
                print(f"Customer {customer.id} is in Teller {id} for {TIME_QUANTUM} seconds")
                teller_service_data[id].append((customer.id,time.time(),time.time()+TIME_QUANTUM))
                customers_served_by_teller[id].append(customer.id)
                time.sleep(TIME_QUANTUM)

                with customer_queue_lock:
                    customer_queue.put(customer)

                print(f"Customer {customer.id} re-enters the Queue")
            else:
                print(f"Customer {customer.id} is in Teller {id} for {customer.burst_time} seconds")
                teller_service_data[id].append((customer.id,time.time(),time.time()+customer.burst_time))
                time.sleep(customer.burst_time)

                customer.completion_time = time.time()
                print(f"Customer {customer.id} leaves Teller {id}")

                calculate_total_time(customer)


def teller_sjf(id):
    while not stop_simulation.is_set() or not customer_queue_sjf.empty():
        if not customer_queue_sjf.empty():
            with customer_queue_lock:
                burst_time,customer_id, customer = customer_queue_sjf.get()

            customer.start_service_time = time.time()
            print(f"Customer {customer.id} is being served by Teller {id}")

            teller_service_data[id].append((customer.id,customer.start_service_time,customer.start_service_time+customer.burst_time))
            customers_served_by_teller[id].append(customer.id)
            
            time.sleep(customer.burst_time)
            customer.completion_time = time.time()
            print(f"Customer {customer.id} leaves Teller {id}")

            calculate_total_time(customer)

def teller_psjf(id):
    while not stop_simulation.is_set() or customer_queue_sjf.empty():
        if not customer_queue_sjf.empty():
            with customer_queue_lock:
                burst_time,customer_id, customer = customer_queue_sjf.get()

            if customer.start_service_time == 0:
                customer.start_service_time = time.time()

            print(f"Customer {customer.id} is in Teller {id} for {customer.burst_time} seconds")
            customers_served_by_teller[id].append(customer_id)
            while(burst_time>0):
                time.sleep(1)
                burst_time-=1
                teller_service_data[id].append((customer_id, time.time(), time.time() + 1))
                if not customer_queue_sjf.empty():
                    with customer_queue_lock:
                        new_burst_time,new_customer_id,new_customer=customer_queue_sjf.get()
                    if new_burst_time<burst_time:
                        with customer_queue_lock:
                            customer_queue_sjf.put((burst_time,customer_id,customer))
                        customer_id=new_customer_id
                        customer=new_customer
                        burst_time=new_burst_time
                        break
                    else:
                        with customer_queue_lock:
                            customer_queue_sjf.put((new_burst_time,new_customer_id,new_customer))
            
            if burst_time<=0:
                customer.completion_time = time.time()
                print(f"Customer {customer.id} leaves Teller {id}")

                calculate_total_time(customer)

    

if __name__ == "__main__":
    algorithm=input("Enter the scheduling algorithm you want to use(fcfs,sjf,psjf,rr): ")

    if algorithm in ['fcfs','rr']:
        customer_generator=threading.Thread(target=customer_arrival,args=(customer_queue,))
    else:
        customer_generator=threading.Thread(target=customer_arrival,args=(customer_queue_sjf,))
    
    customer_generator.start()

    if algorithm == 'fcfs':
        teller_function=teller_fcfs
    elif algorithm == 'rr':
        teller_function=teller_rr
    elif algorithm=='sjf':
        teller_function=teller_sjf
    elif algorithm=='psjf':
        teller_function=teller_psjf
    else:
        print("Invalid Algorithm")
        stop_arrival.set()
        customer_generator.join()
        exit()

    tellers = []
    for teller_id in range(NUM_TELLERS):
        teller= threading.Thread(target=teller_function, args=(teller_id + 1,))
        teller.start()
        tellers.append(teller)

    stop_customer_generator = threading.Thread(target=stop_simulation_on_keypress)
    stop_customer_generator.start()

    stop_customer_generator.join()
    customer_generator.join()

    stop_simulation.set()
    for teller in tellers:
        teller.join()

    avg_times = calculate_average_time()
    plot_average_time_and_teller_service_data(avg_times)
