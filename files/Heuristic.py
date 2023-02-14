from rectpack import newPacker

def read_input(file_path):
    with open(file_path) as f:
        rect_count, truck_count = map(int, f.readline().split())
        rects, trucks = list(), list()

        for _ in range(rect_count):
            rects.append(tuple(map(int, f.readline().split())))

        for _ in range(truck_count):
            trucks.append(tuple(map(int, f.readline().split())))

    return rect_count, truck_count, rects, trucks

def area(tup):
    '''return the area of rect or truck, generally called tup (stands for tuple)'''
    return tup[0] * tup[1]


def fee_per_area(truck):
    '''return fee per area of the truck'''
    return truck[2] / (truck[0]*truck[1])

def best_score(remaining_area, truck):
    return max(remaining_area - truck[0]*truck[1], 0) 

if __name__ == '__main__':
    
    file_path = 'files/generated_data/1000.txt'

    #limit the time taken per iteration to reduce runtime at the cost of maybe skipped a better optimized solution
    GLOBAL_TIME_LIMIT_PER_ITER = 0.1

    rect_count, truck_count, rects, trucks = read_input(file_path)

    # rects: sort them by area in descending order
    rects.sort(key=area, reverse=True)

    # trucks: sort them by fee per area in ascending order
    trucks.sort(key=fee_per_area)

    rect_in_truck_no= [0 for _ in range(rect_count)]
    
    packer=newPacker(mode=1,bin_algo=3)

    for r in rects:
        packer.add_rect(*r)

    for i in range(len(trucks)):
        packer.add_bin(trucks[i][0],trucks[i][1],bid=trucks[i][2])

    packer.pack()

    nbins=len(packer)

    print('Number of bin used:',nbins)
    print('total cost: ', sum(atruck.bid for atruck in packer) )
    
    packer2=newPacker(mode=1,bin_algo=3)

    for r in rects:
        packer.add_rect(*r)

    for i in range(len(trucks)):
        packer.add_bin(trucks[i][0],trucks[i][1],bid=trucks[i][2])

    packer.pack()
 