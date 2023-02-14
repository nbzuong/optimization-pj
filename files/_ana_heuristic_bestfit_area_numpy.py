from copy import deepcopy
import time

import numpy as np
from numpy.core.fromnumeric import shape

import pandas as pd
import pickle as pkl

# -------------------------------- FIT --------------------------------
class FitSolutionFound(Exception):
    '''throw if a fit is found'''
    pass


class TimeExceededError(Exception):
    '''throw if time for an iteration of fit exceeded GLOBAL_TIME_LIMIT_PER_ITER'''
    pass


def fitable_not_rotated(rect, a, i, j):
    '''
    check if the rect fit the truck array a at the coordinate (i, j),
    without rotating
    '''
    try:
        if (a[i: i+rect[0], j: j+rect[1]] == 1).any():
            return False
    except IndexError:
        return False
    return True


def fitable_rotated(rect, a, i, j):
    '''
    check if the rect fit the truck array a at the coordinate (i, j),
    after rotating
    '''
    try:
        if (a[i: i+rect[1], j: j+rect[0]] == 1).any():
            return False
    except IndexError:
        return False
    return True


def fitable(rect, a, i, j):
    '''
    check if the rect fit the truck array a at the coordinate (i, j)
        return None if not fit,
        return True if don't need to rotate
        return False if need to rotate
    '''
    if fitable_not_rotated(rect, a, i, j):
        return True
    elif fitable_rotated(rect, a, i, j):
        return False
    else:
        return None


def insert_remove(rect, a, i, j, not_rotate, value=1):
    '''
    return
        a[i:i+rect[0], j:j+rect[1]] = value if not_rotate == True
        or
        a[i:i+rect[1], j:j+rect[0]] = value if not_rotate == False
    if a is numpy array
    '''
    a = deepcopy(a)
    if not_rotate:
        a[i: i+rect[0], j: j+rect[1]] = value
    else:
        a[i: i+rect[1], j: j+rect[0]] = value
    return a


def fit(rects_to_fit, truck_to_fit):
    '''check if all rects in rects_to_fit fit the truck_to_fit'''  # scuse me wtf? 
    global ITER_time_start

    def fit_run(rects_left:list, truck:tuple, a:list):
        '''run the algo'''
        nonlocal res
        # if there is no rect left, so every rect have fitted in the truck
        # so the function fit is True
        if not rects_left:
            res = True
            raise FitSolutionFound

        # if there is a rect, pop it out then continue to run...
        else:
            rect = rects_left.pop(0)

            # try it in every place of the truck
            for i in range(truck[0]):
                for j in range(truck[1]):
                    # check the timer, if it exceeded the configured time limit
                    # throw TimeExceededError to skip the current truck
                    if time.time() - ITER_time_start > GLOBAL_TIME_LIMIT_PER_ITER:
                        raise TimeExceededError
                    
                    # if not exceeded, check if the rect is fit in the place
                    # if it do, fill the occupied space in a with 1s
                    # then recursively run with the popped list of rects and the new a
                    fitable_var = fitable(rect, a, i, j)
                    if fitable_var is not None:
                        a = deepcopy(insert_remove(rect, a, i, j, fitable_var, value=1))
                        fit_run(rects_left, truck, a)
                        a = deepcopy(insert_remove(rect, a, i, j, fitable_var, value=0))

            # reappend the popped rect
            # most of the time, this will not run, but imma do it just to be safe
            rects_left.append(rect)

    # result
    res = False

    # init a
    # a is the list of lists of ints (2d int array) to indicate the current state of the truck
    # where 0 is not occupied, 1 otherwise
    a = np.zeros((truck_to_fit[0], truck_to_fit[1]), dtype=int)

    # try to fit all rects in the truck
    try:
        fit_run(rects_left=rects_to_fit,
                        truck=truck_to_fit,
                        a=a,
        )
    # if FitSolutionFound is thrown, stop it right away to save time
    except FitSolutionFound:
        pass

    return res


# -------------------------------- READ INPUT --------------------------------
def read_input(file_path):
    with open(file_path) as f:
        rect_count, truck_count = map(int, f.readline().split())
        rects, trucks = list(), list()

        for _ in range(rect_count):
            rects.append(tuple(map(int, f.readline().split())))

        for _ in range(truck_count):
            trucks.append(tuple(map(int, f.readline().split())))

    return rect_count, truck_count, rects, trucks


# -------------------------------- UTILITIES --------------------------------
def area(tup):
    '''return the area of rect or truck, generally called tup (stands for tuple)'''
    return tup[0] * tup[1]


def fee_per_area(truck):
    '''return fee per area of the truck'''
    return truck[2] / (truck[0]*truck[1])


def used_trucks_indices(rects_contained):
    '''a list of indices of used trucks, given the rects in trucks'''
    return [index for index, lst in enumerate(rects_contained) if lst]


def total_cost(trucks, used_trucks_indices_var):
    '''return the total cost, given the indices of the trucks used'''
    return sum(truck[2] for index, truck in enumerate(trucks) if index in used_trucks_indices_var)


# -------------------------------- MAIN --------------------------------
if __name__ == '__main__':
    np.set_printoptions(suppress=True)

    rect_counts = [i for i in range(5, 50)] + \
                  [i for i in range(50, 200, 50)] + \
                  [i for i in range(200, 1001, 200)] +\
                    ['_sample_data']
    directory = 'files/generated_data'

    ana_data = list()
    
    for rect_count in rect_counts:
        if isinstance(rect_count, int): 
            file_path = f'{directory}/{str(rect_count).zfill(4)}.txt'
        else:
            file_path = f'{directory}/{rect_count}.txt'

        # GLOBAL_TIME_LIMIT_PER_ITER should be >= 0.01,
        # else the algorithm might be so bad, or worst, running infinitely long. 
        # A good time limit should be between 0.1 and 10 seconds.
        GLOBAL_TIME_LIMIT_PER_ITER = 1
        # file_path = 'files/generated_data/1000.txt'
        # removing prints (SILENT = True) 
        # possibly result in a lower running time, about from 0.1 to 1 second
        SILENT = True

        # -------------------------------- READ INPUT --------------------------------
        rect_count, truck_count, rects, trucks = read_input(file_path)
        if not SILENT:
            print('-------------------- INPUT --------------------')
            print(rect_count)
            print(rects)
            print(truck_count)
            print(trucks)
            print()

        # -------------------------------- START TIMER --------------------------------
        GLOBAL_time_start = time.time()

        # -------------------------------- SORT --------------------------------
        # rects: sort them by area in descending order
        rects.sort(key=area, reverse=True)

        # trucks: sort them by fee per area in ascending order
        trucks.sort(key=fee_per_area)
        
        if SILENT:
            print('Running silently... Just wait...')
        else:
            print('-------------------- SORTED LISTS --------------------')
            print(rects)
            print(trucks)
            print('-------------------- RUN --------------------')

        # -------------------------------- INITIALIZE --------------------------------
        # area left in each truck
        areas_left: list[int] = [area(truck) for truck in trucks]
        # list of rect contained in each truck
        rects_contained: list[list] = [list() for _ in range(len(trucks))]
        time_exceeded_count = 0  
        
        # -------------------------------- RUN BEST-FIT HEURISTIC --------------------------------
        while rects:
            # -------------------------------- TAKE A RECT --------------------------------
            if not SILENT:
                print(f'Number of rects left: {len(rects)}')

            rect = rects.pop(0)
            area_rect = area(rect)

            # -------------------------------- ITERATE THROUGH truckS --------------------------------
            for index, (truck, area_left, rects_contained_in_truck) in \
                    enumerate(zip(trucks, areas_left, rects_contained)):
                # skip the truck if the rect is bigger than the area left 
                if area_left < area_rect:
                    continue
                
                # start the timer for each truck
                ITER_time_start = time.time()

                # try to fit the rect + previous rects currently in the truck
                try:
                    # in fit(), the TimeExceededError is thrown if the time exceeded
                    if fit(rects_contained_in_truck+[rect], truck):
                        # reduce the area left of the truck
                        areas_left[index] -= area_rect
                        # add the rect to the list of rects already in the truck
                        rects_contained[index].append(rect)
                        # break out of the truck loop
                        break

                except TimeExceededError:
                    # count the number of times the iteration's running time exceeded limit
                    time_exceeded_count += 1
                    if not SILENT:
                        print(f'#{index} Iteration, #{len(rects)+1} rect: The iteration exceeded {GLOBAL_TIME_LIMIT_PER_ITER} second(s) limit, skipped a potential better solution')
                    continue

        # -------------------------------- PRINT SOLUTION --------------------------------
        GLOBAL_time_end = time.time()

        # print('-------------------- SOLUTION --------------------')
        # print('THE SOLUTION FOUND:')
        # print(rects_contained)

        used_trucks_indices_var = used_trucks_indices(rects_contained)
        # print(f'NUMBER OF truckS USED: {len(used_trucks_indices_var)}')
        
        # print(f'COST: {total_cost(trucks, used_trucks_indices_var)}')

        # print('-------------------- OTHER STATS --------------------')
        # print(f'Total running time: {GLOBAL_time_end - GLOBAL_time_start}')
        # print(f'Time limited per iteration: {GLOBAL_TIME_LIMIT_PER_ITER}')
        # print(f'Number of iterations skipped: {time_exceeded_count}')

        ana_data.append(
            [
                rect_count,
                truck_count,
                total_cost(trucks, used_trucks_indices_var),
                len(used_trucks_indices_var),
                GLOBAL_time_end - GLOBAL_time_start,
                GLOBAL_TIME_LIMIT_PER_ITER,
                time_exceeded_count,
            ])

    df = pd.DataFrame(
        ana_data,
        columns=['rect_count', 'truck_count', 'total cost', 'trucks used count',
                 'running time', 'GLOBAL_TIME_LIMIT_PER_ITER', 'time_exceeded_count']
    )
    print(df)

    df.to_csv(f'files/_analytical_data/_ana_heuristic_bestfit_area_numpy_{str(GLOBAL_TIME_LIMIT_PER_ITER)}.csv')
    with open(f'files/_analytical_data/_ana_heuristic_bestfit_area_numpy_{str(GLOBAL_TIME_LIMIT_PER_ITER)}.pkl', 'wb') as f:
        pkl.dump(df, f)