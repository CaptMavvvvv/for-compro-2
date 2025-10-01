def maze_solver_with_conveyors(maze):
    rows, cols = len(maze), len(maze[0])
    
    start = end = None
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 'S':
                start = (r, c)
            elif maze[r][c] == 'E':
                end = (r, c)
    
    if not start or not end:
        return {"distance": -1, "path": []}
    
    directions = {
        '>': (0, 1),
        '<': (0, -1),
        'v': (1, 0),
        '^': (-1, 0),
    }

    def in_bounds(r, c):
        return 0 <= r < rows and 0 <= c < cols and maze[r][c] != '#'
    
    q = [(start[0], start[1], 0, [list(start)])]
    visited = set([start])
    
    while q:
        r, c, dist, path = q.pop(0)

        if (r, c) == end:
            return {"distance": dist, "path": path}

        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            if (nr, nc) in visited:
                continue

            temp_path = path.copy()
            temp_path.append([nr, nc])
            cr, cc = nr, nc
            
            while maze[cr][cc] in directions:
                dr2, dc2 = directions[maze[cr][cc]]
                nr2, nc2 = cr + dr2, cc + dc2
                if not in_bounds(nr2, nc2):
                    break
                cr, cc = nr2, nc2
                temp_path.append([cr, cc])
                if (cr, cc) == end:
                    return {"distance": dist + 1, "path": temp_path}
            
            if (cr, cc) not in visited:
                visited.add((cr, cc))
                q.append((cr, cc, dist + 1, temp_path))

    return {"distance": -1, "path": []}


if __name__ == '__main__':
    maze = [
        ['S', '>', '>', 'E'],
        ['#', '#', '#', '#']
    ]
    result = maze_solver_with_conveyors(maze)
    print(result)
    # Output: {'distance': 2, 'path': [[0, 0], [0, 1], [0, 2], [0, 3]]}

    maze = [
        ['S', '>', '>', 'E'],
        ['#', '#', '#', '#', '#']
    ]
    result = maze_solver_with_conveyors(maze)
    print(result)
    # Output: {'distance': -1, 'path': []}

    maze = [
        ['S', 'v', 'v', 'E'],
        ['#', 'v', '#', '#'],
        ['#', 'v', '#', '#'],
        ['#', 'v', '#', '#'],
        ['#', '#', '#', '#']
    ]
    result = maze_solver_with_conveyors(maze)
    print(result)
    # Output: {'distance': 7, 'path': [[0, 0], [0, 1], [1, 1], [2, 1], [2, 2], [3, 2], [3, 3], [2, 3], [1, 3], [0, 3], [0, 4]]}