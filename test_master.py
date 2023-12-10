from main import main


def worker(addr):
    addr_list = [("127.0.0.1", 8000), ("127.0.0.1", 8001), ("127.0.0.1", 8002)]
    configs = { "key": "value", 
            'k': 2,   
            "database": "data/databases/test.txt",
            "patterns": [
                "data/patterns/medium.txt",
                "data/patterns/test.txt"
            ]}
    main(addr_list, addr, configs)



worker(("127.0.0.1", 8000))
