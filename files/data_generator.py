from math import ceil
import random as rd
from copy import Error, deepcopy
import sys

import numpy as np
import matplotlib.pyplot as plt


def plot_full_truck_and_cut_truck(truck_array, removed_array, shape, len_trucks):
    plt.plot([0, shape[1], shape[1]], [shape[0], shape[0], 0], 'red')
    plt.imshow(truck_array, cmap='turbo', extent=(0,25,25,0), vmin=-1, vmax=5)
    plt.savefig(f'files/generated_figures/{len_trucks}_A')
    plt.clf()

    plt.imshow(removed_array, cmap='turbo', extent=(0,shape[1],shape[0],0), vmin=-1, vmax=5)
    plt.savefig(f'files/generated_figures/{len_trucks}_B')
    plt.clf()


def plot_building_solution(truck_array, available_places):
    plt.imshow(truck_array, cmap='turbo', extent=(0,25,25,0), vmin=-1, vmax=5)
    for place in available_places:
        plt.text(place[1]+0.5, place[0], 'x', ha='center', va='top', c='white')
    plt.savefig(f'files/generated_figures/{len(available_places)}')
    plt.clf()


def rd_a_rect() -> tuple[int, int]:
    '''random a rectangle, return size'''
    return rd.randrange(1, 6), rd.randrange(1, 6)


def rd_some_rects(rect_count: int) -> list[tuple[int, int]]:
    '''random rect_count rectangles, return a list of sizes'''
    return [rd_a_rect() for _ in range(rect_count)]


def rd_pick_some_rects(rects) -> tuple[list, list]:
    '''
    randomly pick and remove some rectangles from rects,
    return a tuple of 2 lists:
        the first list is the reduced list of rectangles,
        the second list is the picked rectangles
    '''
    rect_count = rd.randrange(2, 6)
    reduced_rects = deepcopy(rects)

    # shuffle the list, then take rectangles from top
    rd.shuffle(reduced_rects)
    picked_rects = reduced_rects[:rect_count]
    reduced_rects = reduced_rects[rect_count:]

    return reduced_rects, picked_rects


def rd_put(rects, save_figures=False) -> np.array:
    '''
    randomly put each rectangle next to each other, as described
    '''
    truck_array = np.full((25, 25), fill_value=-1, dtype=int)
    available_places = [(0, 0)]

    for rect_index, rect in enumerate(rects):
        while True:
            # pick a random place to put
            rd.shuffle(available_places)
            place = available_places.pop(0)

            x_start, y_start = place
            x_end, y_end = x_start + rect[0], y_start + rect[1]

            # only put if puttable
            check_area_to_put = truck_array[x_start : x_end, y_start : y_end] == -1
            if check_area_to_put.all():
                truck_array[x_start : x_end, y_start : y_end] = rect_index
                break
        
        # remove old places
        for x in range(x_start, x_end):
            for y in range(y_start, y_end):
                try:
                    available_places.remove((x, y))
                except ValueError:
                    pass

        # add new places
        new_avalable_places = [(x_end, y) for y in range(y_start, y_end)]
        new_avalable_places += [(x, y_end) for x in range(x_start, x_end)]

        available_places += new_avalable_places

        # plot if save_figures
        if save_figures:
            plot_building_solution(truck_array, available_places)

    return truck_array


def shape_after_remove_redundant(truck_array: np.array) -> tuple:
    '''size remove redundant row and col, which are filled by -1'''
    array_size = list(truck_array.shape)

    current_row_index = -1  # init by lowest row
    while True:
        if (truck_array[current_row_index] == -1).all():
            array_size[0] -= 1
            current_row_index -= 1
        else:
            break
    
    current_col_index = -1  # init by right most col
    while True:
        if (truck_array[:, current_col_index] == -1).all():
            array_size[1] -= 1
            current_col_index -= 1
        else:
            break

    return tuple(array_size)
    

def remove_redundant(truck_array: np.array, shape: tuple):
    return truck_array[:shape[0], :shape[1]]


def rd_truck_cost():
    '''from 100 to 1000, step is 50'''
    return rd.randrange(100, 1001, 50)


def rd_truck_size():
    '''from 1 to 25 each side, used only after fitting previous trucks'''
    return rd.randrange(1, 26), rd.randrange(1, 26)





if __name__ == '__main__':
    if input('Type Y to generate: ') not in ['y', 'Y']:
        raise Error('Type Y to generate')

    np.set_printoptions(threshold=sys.maxsize, linewidth=sys.maxsize)

    # numbers of rectangles based on difficulty (index)
    rect_counts = [i for i in range(5, 55)] + \
                  [i for i in range(60, 331, 30)] + \
                  [i for i in range(350, 1000, 50)] +\
                    [i for i in range(1000, 5001, 1000)]
    print('rect_counts:', rect_counts)
    print('len:', len(rect_counts))
    print()

    # seed
    seed = 69420
    rd.seed(seed)
    print('RANDOMIZING with seed:', seed)
    print()

    # generate and save
    for index_difficulty, rect_count in enumerate(rect_counts):
        # create rects randomly
        rects = rd_some_rects(rect_count)

        # create trucks with rects
        copy_rects = deepcopy(rects)  # save to recover later
        trucks = list()  # list of tuples of size, cost not included

        while rects:
            # save figures of: BUILD 6TH truck OF DIFFICULTY 25
            rects, picked_rects = rd_pick_some_rects(rects)
            truck_array = rd_put(picked_rects,
                               save_figures=index_difficulty==25 and len(trucks)==5)
            shape = shape_after_remove_redundant(truck_array)
            trucks.append(shape)

            # save figures of: all trucks of difficulty 25
            if index_difficulty == 25:
                plot_full_truck_and_cut_truck(truck_array, remove_redundant(truck_array, shape), shape, len(trucks))

        trucks += [rd_truck_size() for _ in range(ceil(len(trucks)/5))]

        rects = copy_rects

        # write to files
        directory = 'files/generated_data'
        file_path = f'{directory}/{str(rect_count).zfill(4)}.txt'

        with open(file_path, 'w') as f:
            f.write(f'{rect_count} {len(trucks)}\n')
            for rect in rects:
                f.write(f'{rect[0]} {rect[1]}\n')
            for truck in trucks:
                f.write(f'{truck[0]} {truck[1]} {rd_truck_cost()}\n')
    
    print('DONE')