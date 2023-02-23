from ortools.linear_solver.pywraplp import Solver
import sys
import time

def input(file_path):   # import the input from filepath
    with open(file_path) as f:
        n_rectangles, n_trucks = [int(x) for x in f.readline().split()]
        rectangles, trucks = [], []

        for _ in range(n_rectangles):
            rectangles.append([int(x) for x in f.readline().split()])

        for _ in range(n_trucks):
            trucks.append([int(x) for x in f.readline().split()])

    return n_rectangles, n_trucks, rectangles, trucks


if __name__ == "__main__":
    try:
        file_path = sys.argv[1]
    except IndexError:
        file_path = 'files/generated_data/0045.txt'
    n_rectangles, n_trucks, rectangles, trucks = input(file_path)
    max_width, max_height = (
        max(trucks, key=lambda x: x[0])[0],
        max(trucks, key=lambda x: x[1])[1],
    )
    
    solver = Solver.CreateSolver("SCIP")
    start=time.time()
    # truck[i] = 1 if it is used
    truck_used  = [solver.IntVar(0, 1, f"truck_used[{i}]") for i in range(n_trucks)]

    # rotate[i] = 1 iff rectangle[i] rotates 90 degree
    rotate      = [solver.IntVar(0, 1, f"rotate[{i}]") for i in range(n_rectangles)]

    # truck_index[i] is the index of the truck in which rectangle[i] should be placed
    truck_index   = [ solver.IntVar(0, n_trucks - 1, f"truck_index[{i}]") for i in range(n_rectangles) ]

    # coordinates
    left = []
    right = []
    top = []
    bottom = []

    for i in range(n_rectangles):
        left.append(solver.IntVar(0, max_width,   f"left[{i}]"))
        right.append(solver.IntVar(0, max_width,   f"right[{i}]"))
        top.append(solver.IntVar(0, max_height,  f"top[{i}]"))
        bottom.append(solver.IntVar(0, max_height,  f"bottom[{i}]"))

        Solver.Add(solver, right[i] == left[i] + rectangles[i][0] * (1 - rotate[i]) + rotate[i] * rectangles[i][1])
        
        Solver.Add(solver, top[i] == bottom[i] + rectangles[i][1] * (1 - rotate[i]) + rotate[i] * rectangles[i][0]) 

    M = 100000

    for i in range(n_rectangles - 1):
        for j in range(i + 1, n_rectangles):
            
            constraints = [
                (right[i], left[j]),
                (right[j], left[i]),
                (top[i], bottom[j]),
                (top[j], bottom[i]),
            ]

            # t = 1 => y <= z
            # t = 0 => y <= M + z => nothing
            t = list()
            for k, (y, z) in enumerate(constraints):
                t.append(Solver.IntVar(solver, 0, 1, f't[{i}][{j}][{k}]'))
                Solver.Add(solver, y <= M * (1 - t[k]) + z)

            # if truck_index[i] == truck_index[j] then b = 1
            # else b == 0

            # got: sum >= 0
            # b = 1 => sum >= 1
            # b = 0 => sum = 0
            b = Solver.IntVar(solver, 0, 1, f'b[{i}][{j}]')
            Solver.Add(solver, sum(t) <= b * M) #block the case where sum(t)>0 <=> there is a plausible way of putting item j next to i but b = 0 <=> i and j not in the same bin 
            Solver.Add(solver, sum(t) + (1 - b) * M >= 1) #block the case where sum(t)= 0 <=> no way to put item j next to i but smh b=1 <=> i and j is in same bin
            
            #ensure that i and j is put inside the same bin
            y = truck_index[i] 
            z = truck_index[j]
            t0 = Solver.IntVar(solver, 0, 1, f't0[{i}][{j}]')
            t1 = Solver.IntVar(solver, 0, 1, f't1[{i}][{j}]')
            t2 = Solver.IntVar(solver, 0, 1, f't2[{i}][{j}]')

            # t0 = 0 => y == z
            # t0 = 1 => y != z
            Solver.Add(solver, z + t0 <= y + M * t1)
            Solver.Add(solver, y + t0 <= z + M * t2)
            Solver.Add(solver, t1 + t2 == t0)

            Solver.Add(solver, b == 1 - t0)

    # add the constraint to check if it is possible to put item i in bin j 
    for i in range(n_rectangles):
        for j in range(n_trucks):
            c = Solver.IntVar(solver, 0, 1, f"c[{i}][{j}]")
            y = truck_index[i]
            z = j
            x0 = Solver.IntVar(solver, 0, 1, f'x0[{i}][{j}]')
            x1 = Solver.IntVar(solver, 0, 1, f'x1[{i}][{j}]')
            x2 = Solver.IntVar(solver, 0, 1, f'x2[{i}][{j}]')

            # x0 = 0 => y == z
            # x0 = 1 => y != z
            Solver.Add(solver, z + x0 <= y + M * x1)
            Solver.Add(solver, y + x0 <= z + M * x2)
            Solver.Add(solver, x1 + x2 == x0)

            # c = 1 => truck_index[i] == j
            # c = 0 => truck_index[i] != j
            Solver.Add(solver, c == 1 - x0)

            # box has to be inside truck
            Solver.Add(solver, right[i]     <= trucks[j][0] + (1 - c) * M)
            Solver.Add(solver, left[i]      <= trucks[j][0] + (1 - c) * M)
            Solver.Add(solver, top[i]       <= trucks[j][1] + (1 - c) * M)
            Solver.Add(solver, bottom[i]    <= trucks[j][1] + (1 - c) * M)

    for j in range(n_trucks):
        is_put_to_truck = [ Solver.IntVar(solver, 0, 1, f"p[{i}][{j}]") for i in range(n_rectangles) ]

        for i in range(n_rectangles):

            d = Solver.IntVar(solver, 0, 1, f"d[{i}][{j}]")
            y = truck_index[i]
            z = j
            q0 = Solver.IntVar(solver, 0, 1, f'q0[{i}][{j}]')
            q1 = Solver.IntVar(solver, 0, 1, f'q1[{i}][{j}]')
            q2 = Solver.IntVar(solver, 0, 1, f'q2[{i}][{j}]')

            # q0 = 0 => y == z
            # q0 = 1 => y != z
            Solver.Add(solver, z + q0 <= y + M * q1)
            Solver.Add(solver, y + q0 <= z + M * q2)
            Solver.Add(solver, q1 + q2 == q0)

            Solver.Add(solver, d == 1 - q0)
            Solver.Add(solver, is_put_to_truck[i]  == d)               

        e = Solver.IntVar(solver, 0, 1, f"e[{i}]")
        Solver.Add(solver, sum(is_put_to_truck)    <= (1 - e) * M)               
        Solver.Add(solver, sum(is_put_to_truck) + e * M >= 1)              
        Solver.Add(solver, truck_used[j]         == 1 - e)          

    # Objective
    cost = sum(truck_used[j] * trucks[j][2] for j in range(n_trucks))
    Solver.Minimize(solver, cost)

    solver.set_time_limit(300 * 1000)

    # Creates solver and solve the model
    status = Solver.Solve(solver)
    end = time.time()
    if status == Solver.OPTIMAL or status == Solver.FEASIBLE:
        
        for i in range(n_rectangles):
            print( f"put rectangle {i + 1} with rotation {rotate[i].solution_value()} in truck {truck_index[i].solution_value() + 1} at {left[i].solution_value()} {bottom[i].solution_value()} -> {right[i].solution_value()} {top[i].solution_value()}" )
        print(f"Min cost: {solver.Objective().Value()}")
        print("truck_used:", len(set([truck_index[i].solution_value() for i in range(n_rectangles)])))
        print("Running_time: ", end-start)
