from ortools.sat.python import cp_model
import sys
from typing import Tuple, List


class _2DBinPackingCP(cp_model.CpModel):

    def __init__(self, file_path: str, time_limit: int = 600) -> None:
        super().__init__()
        self.file_path = file_path
        self.solver = cp_model.CpSolver()
        # time limit
        self.solver.parameters.max_time_in_seconds = time_limit

    def __input(self, file_path: str) -> Tuple[int, int, List, List]:
        with open(file_path) as f:
            n_rectangles, n_trucks = [int(x) for x in f.readline().split()]
            rectangles, trucks = [], []

            for _ in range(n_rectangles):
                # width and weight of rectangle
                rectangles.append([int(x) for x in f.readline().split()])

            for _ in range(n_trucks):
                # width, height and cost of truck
                trucks.append([int(x) for x in f.readline().split()])

        return n_rectangles, n_trucks, rectangles, trucks

    def __set_variables_and_constraints(self) -> None:
        # read input data
        self.n_rectangles, self.n_trucks, self.rectangles, self.trucks = self.__input(self.file_path)

        # (weak) upper bound of coordinates
        self.max_width, self.max_height = max(self.trucks, key=lambda x: x[0])[0], max(self.trucks, key=lambda x: x[1])[1]

        # truck[i] = 1 iff it is used
        self.is_use_truck = [self.NewIntVar(0, 1, f'is_use_truck[{i}]') for i in range(self.n_trucks)]

        # rotate[i] = 1 iff rectangle[i] rotates 90 degree
        self.rotate = [self.NewIntVar(0, 1, f'rotate[{i}]') for i in range(self.n_rectangles)]

        # truck_index[i] is the index of the truck in which rectangle[i] should be placed
        self.truck_index = [self.NewIntVar(0, self.n_trucks - 1, f'truck_index[{i}]') for i in range(self.n_rectangles)]

        # coordinates
        self.left = []
        self.right = []
        self.top = []
        self.bottom = []

        for i in range(self.n_rectangles):
            # weak upper bound
            self.left.append(self.NewIntVar(0, self.max_width, f'left[{i}]'))
            self.right.append(self.NewIntVar(0, self.max_width, f'right[{i}]'))
            self.top.append(self.NewIntVar(0, self.max_height, f'top[{i}]'))
            self.bottom.append(self.NewIntVar(0, self.max_height, f'bottom[{i}]'))

            self.Add(self.right[i] == self.left[i] + self.rectangles[i][0]).OnlyEnforceIf(self.rotate[i].Not())
            self.Add(self.right[i] == self.left[i] + self.rectangles[i][1]).OnlyEnforceIf(self.rotate[i])
            self.Add(self.top[i] == self.bottom[i] + self.rectangles[i][1]).OnlyEnforceIf(self.rotate[i].Not())
            self.Add(self.top[i] == self.bottom[i] + self.rectangles[i][0]).OnlyEnforceIf(self.rotate[i])

        for i in range(self.n_rectangles - 1):
            for j in range(i + 1, self.n_rectangles):
                b1 = self.NewBoolVar(f'b1[{i}][{j}]')
                t1 = self.NewIntVar(0, 1, f't1[{i}][{j}]')
                self.Add(self.right[i] <= self.left[j]).OnlyEnforceIf(b1)
                self.Add(t1 == 1).OnlyEnforceIf(b1)
                self.Add(t1 == 0).OnlyEnforceIf(b1.Not())

                b2 = self.NewBoolVar(f"b2[{i}][{j}]")
                t2 = self.NewIntVar(0, 1, f"t2[{i}][{j}]")
                self.Add(self.right[j] <= self.left[i]).OnlyEnforceIf(b2)
                self.Add(t2 == 1).OnlyEnforceIf(b2)
                self.Add(t2 == 0).OnlyEnforceIf(b2.Not())

                b3 = self.NewBoolVar(f"b3[{i}][{j}]")
                t3 = self.NewIntVar(0, 1, f"t3[{i}][{j}]")
                self.Add(self.top[i] <= self.bottom[j]).OnlyEnforceIf(b3)
                self.Add(t3 == 1).OnlyEnforceIf(b3)
                self.Add(t3 == 0).OnlyEnforceIf(b3.Not())

                b4 = self.NewBoolVar(f"b4[{i}][{j}]")
                t4 = self.NewIntVar(0, 1, f"t4[{i}][{j}]")
                self.Add(self.top[j] <= self.bottom[i]).OnlyEnforceIf(b4)
                self.Add(t4 == 1).OnlyEnforceIf(b4)
                self.Add(t4 == 0).OnlyEnforceIf(b4.Not())

                # non-overlap: if two self.rectangles are putted into the same truck, one of 4 conditions above must be satisfied
                b0 = self.NewBoolVar('b0')
                self.Add(self.truck_index[i] == self.truck_index[j]).OnlyEnforceIf(b0)
                self.Add(self.truck_index[i] != self.truck_index[j]).OnlyEnforceIf(b0.Not())
                self.Add(t1 + t2 + t3 + t4 >= 1).OnlyEnforceIf(b0)
                self.Add(t1 + t2 + t3 + t4 == 0).OnlyEnforceIf(b0.Not())

        # if truck_index[i] = j, i.e. rectangles[i] is putted in trucks[j], its width and height must fit this truck (tight upper bound)
        for i in range(self.n_rectangles):
            for j in range(self.n_trucks):
                c = self.NewBoolVar('c')
                self.Add(self.truck_index[i] == j).OnlyEnforceIf(c)
                self.Add(self.truck_index[i] != j).OnlyEnforceIf(c.Not())
                self.Add(self.right[i] <= self.trucks[j][0]).OnlyEnforceIf(c)
                self.Add(self.top[i] <= self.trucks[j][1]).OnlyEnforceIf(c)

        for j in range(self.n_trucks):
            # is_put_to_truck[i] = 0 means that rectangle[i] not in the current truck
            is_put_to_truck = [self.NewIntVar(0, 1, f'{i}') for i in range(self.n_rectangles)]
            for i in range(self.n_rectangles):
                
                d = self.NewBoolVar('d')
                
                self.Add(self.truck_index[i] == j).OnlyEnforceIf(d)
                
                self.Add(is_put_to_truck[i] == 1).OnlyEnforceIf(d)
                
                self.Add(self.truck_index[i] != j).OnlyEnforceIf(d.Not())
                
                self.Add(is_put_to_truck[i] == 0).OnlyEnforceIf(d.Not())
            
            e = self.NewBoolVar('e')
            
            self.Add(sum(is_put_to_truck) == 0).OnlyEnforceIf(e)
            
            self.Add(self.is_use_truck[j] == 0).OnlyEnforceIf(e)
            
            self.Add(sum(is_put_to_truck) != 0).OnlyEnforceIf(e.Not())
            
            self.Add(self.is_use_truck[j] == 1).OnlyEnforceIf(e.Not())

    def __objective(self) -> None: # Objective function: minimize the total cost
        
        self.cost = sum(self.is_use_truck[j] * self.trucks[j][2] for j in range(self.n_trucks))
        self.Minimize(self.cost)

    def __print_solution(self) -> None:
        print('-------------------- SOLUTION --------------------')
        print('THE SOLUTION FOUND:')
        for i in range(self.n_rectangles):
            print(
                f'put rectangle {i + 1} with rotate: {self.solver.Value(self.rotate[i])}, in truck {self.solver.Value(self.truck_index[i]) + 1}, at left: {self.solver.Value(self.left[i])} and bottom: {self.solver.Value(self.bottom[i])}')

        print(f'NUMBER OF TRUCKS USED: {sum(self.solver.Value(self.is_use_truck[i]) for i in range(self.n_trucks))}')

        print(f'COST: {self.solver.ObjectiveValue()}')

        print('-------------------- OTHER STATS --------------------')
        print(f'Status   : {self.solver.StatusName(self.status)}')
        #print(f'Initial conflicts: {self.solver.NumConflicts()}')
        print(f'Explored branches : {self.solver.NumBranches()}')
        print(f'Running time: {self.solver.UserTime()} seconds')

    def solve(self) -> None:
        self.__set_variables_and_constraints()
        self.__objective()
        self.status = self.solver.Solve(self)

        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            self.__print_solution()
        else:
            print('NO SOLUTION FOUND.')


def main():
    try:
        file_path = sys.argv[1]
    except IndexError:
        file_path = 'files/generated_data/1000.txt'

    time_limit = 600
    model = _2DBinPackingCP(file_path, time_limit)
    model.solve()


if __name__ == '__main__':
    main()
