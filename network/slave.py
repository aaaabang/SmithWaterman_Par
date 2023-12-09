import pickle
import queue
from .base import StrategyBase
from alg.alg import fill_matrix, trace_back
import time
from .constant import key_value as kv
from alg import files
from alg.seq import read_fna
# from .master import Master
import json

class Slave(StrategyBase):
    def __init__(self, client):
        super().__init__(client)
        self.job_queue = queue.Queue()
        self.client = client
        self.rank = client.rank # rank of this slave 
        self.last_heartbeat_time = time.time()
        self.master_addr = client.master_addr
        master_addr = self.client.addr_list[0]
        with open('config.json', 'r') as f:
            self.configs = json.load(f)
        
        # 停止任务的标志
        self.master_timed_out = False
        self.stop_current_task = False

#already done
    def send_heartbeat_response(self):
        # response heartbeat
        data = "Heartbeat Response"
        data = pickle.dumps(data)
        self.client.send(self.master_addr, data)
        print(f"Slave {self.rank} responses Heartbeat to {self.master_addr}")
        

    def check_if_master_alive(self, timeout=5):
        current_time = time.time()
        if (current_time - self.last_heartbeat_time) > timeout and not self.master_timed_out:
            # if the master timeout
            print('Master is considered as timed out.')
            self.handle_master_timeout()



#computing functions
    def handle_fillmatrix(self, data):
        # 从Master接收到的数据
        '''
            data = {
                    "start_ind": 0,
                    "end_ind": 0,
                    "i_subvec": 0,
                    "subvec": [],
                    "i_th_pattern": 0,
                }
        '''
        # test
        # with open(self.configs['patterns'], 'r') as f:
        #     content = f.read()
        # print(f"Content: {content}")


        # 从文件系统读对应的sequence, pattern
        i_th_pattern = data['i_th_pattern'] # 0, 1, 2, 3
        sequence = read_fna(self.configs['database'], data['start_ind'], data['end_ind'])
        print(f"sequence: {sequence}") # test

        pattern = read_fna(self.configs['patterns'][i_th_pattern], 0, float('inf'))
        print(f"pattern: {pattern}") # test

        N = len(sequence)
        M = len(pattern)    
        print(N, M) # test
        
        # 计算第一个subvec的长度, 用于判断传给fillmatrix的pattern的长度
        if data['i_subvec'] == 0:
            subvec_length = len(data['subvec'])

        # 计算一个 pattern 要划分成几个 subvec
        num_subvecs, remainder = divmod(M, subvec_length)
        num_subvecs += remainder > 0

        #如果是第一块, upvec传空, 否则传上一块的最后一行
        # up_vec = [0,0]
        up_vec = [0 for _ in range(N)] if data['i_subvec'] == 0 else self.previous_bottom_vec
        # print(len(up_vec)) 
        

        

        #for data['i_subvec'] in range(num_subvecs):
        if data['i_subvec'] < num_subvecs - 1:
            pattern_subvec = pattern[data['i_subvec'] * subvec_length : (data['i_subvec'] + 1) * (subvec_length-1)]
            print(f"pattern_subvec: {pattern_subvec}")
            print(f"sequence: {sequence}")
            # print(f"up_vec: {up_vec}")
            print(f"data['i_subvec']: {data['i_subvec']}")
            print(f"data['start_ind']: {data['start_ind']}")
            print(f"data['end_ind']: {data['end_ind']}")
            print(f"self.client.K: {self.configs['k']}")
            right_vec, bottom_vec, topK_dict = fill_matrix( data['subvec'], up_vec, data['i_subvec'], sequence, pattern_subvec, self.configs['k'])
            print("bottom_vec: ", bottom_vec)
            self.previous_bottom_vec = bottom_vec
            response_data = {
                'start_ind': data['start_ind'],
                'end_ind': data['end_ind'],
                'i_subvec': data['i_subvec'],
                'subvec': right_vec,
                'topK': topK_dict,
                'done': False
            }
            self.send_fillmatirx(response_data)
            # test
            print(response_data)

        elif data['i_subvec'] == num_subvecs - 1:
            pattern_subvec = pattern[data['i_subvec'] * subvec_length :]
            right_vec, bottom_vec, topK_dict = fill_matrix( data['subvec'], up_vec, data['i_subvec'], sequence, pattern_subvec, self.configs['k'])
            response_data = {
                'start_ind': data['start_ind'],
                'end_ind': data['end_ind'],
                'i_subvec': data['i_subvec'],
                'subvec': right_vec,
                'topK': topK_dict,
                'done': True
            }
            # self.send_fillmatirx(response_data)

     


    def send_fillmatirx(self, data):
        # 将结果发送回 Master
        data_str = json.dumps(data)
        data_bytes = data_str.encode('utf-8')
        self.client.send(self.master_addr,data_bytes)
        print(f"Slave {self.rank} sends fillmatrix result to {self.master_addr}")
        

    # trace_back(topK, start_s, end_s)
    def handle_traceback(self, data):
        # 从Master接收到的数据
        '''
         data = {'type' : kv.T_TYPE,
            'i_th_pattern' : i_th_pattern,
            'topk_pos' : topk["pos"],
            'topk_value' : topk["val"],
            'start_ind' : topk["start_ind"],
            'end_ind' : topk["end_ind"]}                       
        '''
        # 从文件系统读对应的sequence, pattern
        i_th_pattern = data['i_th_pattern'] # 0, 1, 2, 3
        sequence = read_fna(self.configs['database'], data['start_ind'], data['end_ind'])
        # print(f"sequence: {sequence}") # test

        pattern = read_fna(self.configs['patterns'][i_th_pattern], 0, float('inf'))
        # print(f"pattern: {pattern}") # test

        # N = len(sequence)
        # M = len(pattern)    
        # print(N, M) # test


        # T_TYPE = "traceback"
        # TOPK_VALUE = "topk_value"
        # TOPK_POS = "topk_pos"

       
        
        # 执行 traceback 任务
        # trace_back(topK, start_s, end_s)
        # 参数：
        # topK - 一个字典 {“value":value,"i_subvec":i_subvec,"xy":(x,y)} #键值待统一       注：y需要从子块坐标变成整块的坐标
        # start_s - K值所在seq子块的起始索引
        # end_s - K值所在seq子块的结束索引

        # 返回：
        # aligned_p_s - pattern的alignment结果
        # aligned_s_s - seq的alignment结果
        topK = {
            "value": data['topk_value'],
            "i_subvec": 0, # TODO
            "xy": data['topk_pos']
        }
        aligned_p_s, aligned_s_s = trace_back(topK, data['start_ind'], data['end_ind'])
        # 将结果发送回 Master
        response_data = {
            'alignment': aligned_s_s,
            'i_th_pattern': i_th_pattern,
            'topk_pos': data['topk_pos'],
            'topk_value': data['topk_value'],
        }
        print("tb_response_data:" , response_data)
        self.send_traceback(response_data)

    def send_traceback(self, data):
        # 将结果发送回 Master
        data_str = json.dumps(data)
        data_bytes = data_str.encode('utf-8')
        self.client.send(self.master_addr,data_bytes)
        print(f"Slave {self.rank} sends traceback result to {self.master_addr}")


    def iter(self):
        # TODO
        # 检查是否收到master的心跳包，如果超时，则处理master超时
        # call alg to fill matrix, traceback
        # send to M
        # while True:
        #     # 检查是否收到master的心跳包，如果超时，则处理master超时
        #     self.check_if_master_alive(timeout=5)
        #    # 处理任务队列中的任务
        #     if not self.job_queue.empty():
        #         task = self.job_queue.get()

        #         if self.stop_current_task:
        #             print("Slave is stopping current task.")
        #             continue  # 跳过当前任务

        #         if task['type'] == 'fillmatrix':
        #             self.handle_fillmatrix(task)
        #         elif task['type'] == 'traceback':
        #             self.handle_traceback(task)

        #     time.sleep(0.1)  # 休眠0.1秒，避免CPU占用过高
    # test
        # self.test_handle_fillmatrix()
        self.test_handle_traceback()
        # pass

    # test
    def test_handle_fillmatrix(self):

    # 创建一个 data 字典
        data = {
            "start_ind": 0,
            "end_ind": 50,
            "i_subvec": 0,
            "subvec": [0,0,0],
            "i_th_pattern": 0,
        }

        # 调用 handle_fillmatrix 方法
        self.handle_fillmatrix(data)

    def test_handle_traceback(self):
        # 创建一个 data 字典
        data = {
            'i_th_pattern' : 0,
            'topk_pos' : (1,2),
            'topk_value' : 6,
            'start_ind' : 0,
            'end_ind' : 10}

        # 调用 handle_traceback 方法
        self.handle_traceback(data)

    #从master接收数据
    def recv(self, addr, data):
        if data:
            data = pickle.loads(data)
            print("receive: ", data)
            if data == 'Heartbeat':
                # 处理心跳包
                self.last_heartbeat_time = time.time()  # 更新最后一次心跳时间
                self.send_heartbeat_response()
                print("Slave received heartbeat from Master")
            # elif data == 'remake':
            #     self.handle_remake_command()
            else:
                self.job_queue.put(data)




    #Crush Handling
#     def handle_master_timeout(self):
#         self.master_timed_out = True
#         print("Handling master timeout...")
#         # 如果slave rank等于master rank+1, 则成为新的master
#         master_rank = 0
#         if self.rank == master_rank + 1: 
#             # if Slave's rank is equal to Master's rank+1, then become the new Master
#             self.become_new_master()    
#         else:
#             self.handle_remake_command()

#         time.sleep(10)
        
#     def become_new_master(self):
#     # 从磁盘重新启动并作为master
#         print(f"Slave {self.rank} is becoming the new Master.")
#        # 重置工作状态
#         self.job_queue.queue.clear()
#         self.stop_current_task = False
#         # 设置为master
#         self.client.close()
#         self.client.reopen_socket()  # 重新打开socket
#         self.client = Master(self.client)  # 创建一个新的Master对象
#         print(f"Slave {self.rank} is becoming the new Master.")
#         self.client.iter()  # 开始执行Master的任务
       
    
#     def handle_remake_command(self):
#         # 处理从master收到的 remake 命令
#         print(f"Slave {self.rank} received 'remake' message. Preparing to reset and connect to the new Master.")
        
#         self.stop_current_task = True  # 设置停止当前任务的标志
#         self.job_queue.queue.clear()  # 清空工作队列
#         print("clear job queue")
        
#         self.connect_to_new_master()
#         print("waiting for connecting to new master")
        
# #TODO
#     def connect_to_new_master(self):
#         # 重新连接到master, 设置为false
#         self.master_timed_out = False
#         master_addr = self.client.addr_list[1]
#         print("Reset complete. Ready to connect to the new Master.")


