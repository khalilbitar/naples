from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

class PerformanceStatistics:
    def __init__(self, lower_limit, num_intervals):
        self.lower_limit = lower_limit
        self.num_intervals = num_intervals
        self.intervals = self.generate_intervals()
        self.interval_counts = [0] * num_intervals
        self.p = [0] * num_intervals
        self.cp = [0] * num_intervals
        self.total_performances = 0

    def generate_intervals(self):
        interval_size = 0.10
        return [f"[{self.lower_limit + i * interval_size:.2f}, {self.lower_limit + (i + 1) * interval_size - 0.01:.2f}]" for i in range(self.num_intervals)]

    def add_performance(self, value):
        index = -1
        value_2 = value * 100
        if value_2 % 10 == 0:
            value_2 = value
            value_2 += 0.01   
            index = int((value_2 - self.lower_limit) // 0.10)
        else:
            index = int((value - self.lower_limit) // 0.10)
        if 0 <= index < self.num_intervals:
            self.interval_counts[index] += 1
            self.total_performances += 1

    def calculate_probabilities(self):
        self.p = [count / self.total_performances for count in self.interval_counts]
    
    def calculate_cp(self):
        cp_bar = [0] * self.num_intervals
        cp_bar[0] = self.p[0]
        for i in range(1, self.num_intervals):
            cp_bar[i] = cp_bar[i-1] + self.p[i]
        for i in range(self.num_intervals):
            self.cp[i] = 1 - cp_bar[i]

    def display_statistics(self):
        stats = []
        stats.append(f"Total Performances: {self.total_performances}")
        for interval, count, probability, cum_prob in zip(self.intervals, self.interval_counts, self.p, self.cp):
            stats.append(f"{interval}: {count} performance(s), Probability: {probability:.2%}, CP(i, j): {cum_prob:.2%}")
        return stats

def calculate_statistics(num_athletes, starting_interval_ll, num_of_intervals, athlete_performances):
    interval_values = [[] for _ in range(num_of_intervals)]
    CP = [[] for _ in range(num_athletes)]

    for i in range(num_athletes):
        athlete_performance = PerformanceStatistics(lower_limit=starting_interval_ll, num_intervals=num_of_intervals)
        performances = athlete_performances[i]

        # # If the user presses Enter without entering values, stop
        # if not performances:
        #     break

        performances = list(map(float, performances.split()))

        for performance in performances:
            athlete_performance.add_performance(performance)
            athlete_performance.calculate_probabilities()
            athlete_performance.calculate_cp()
            CP[i] = athlete_performance.cp
            add_interval_value(interval_values=interval_values, value=performance, lower_limit=starting_interval_ll)

    averages = np.zeros(num_of_intervals)
    L = [1] * num_of_intervals
    B = [0] * num_of_intervals
    S = [0] * num_of_intervals
    B[0] = 1 - L[0]
    S[0] = B[0]

    def calc_averages():
        for j in range(num_of_intervals):
            if len(interval_values[j]) > 0:
                averages[j] = np.mean(interval_values[j])
            else:
                averages[j] = 0

    def calc_L():
        for j in range(num_of_intervals):
            for i in range(num_athletes):
                L[j] *= CP[i][j] 

    def calc_B():
        for j in range(num_of_intervals):
            B[j] = 1 - L[j] - S[j-1]
            S[j] = B[j] + S[j-1]

    def calc_naples():
        NAPLES = 0
        se = 0
        for j in range(num_of_intervals):
            NAPLES += B[j] * averages[j]
            se += B[j] * averages[j]**2
        se -= NAPLES**2
        se = np.sqrt(se)
        return NAPLES, se

    calc_averages()
    calc_L()
    calc_B()
    NAPLES, se = calc_naples()

    return NAPLES, se

def add_interval_value(interval_values, value, lower_limit):
    index = -1
    value_2 = value * 100
    if value_2 % 10 == 0:
        value_2 = value
        value_2 += 0.01   
        index = int((value_2 - lower_limit) // 0.10)
    else:
        index = int((value - lower_limit) // 0.10)
    if 0 <= index < len(interval_values):
        interval_values[index].append(value)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_athletes = int(request.form['numAthletes'])
        starting_interval_ll = float(request.form['lowerLimit'])
        num_of_intervals = int(request.form['numIntervals'])

        athlete_performances = []
        for i in range(num_athletes):
            athlete_performances.append(request.form[f'athlete{i+1}Performances'])

        NAPLES, se = calculate_statistics(num_athletes, starting_interval_ll, num_of_intervals, athlete_performances)

        return render_template('result.html', naples=NAPLES, se=se, numAthletes=num_athletes)

    return render_template('index.html', numAthletes=1)  # Corrected line



if __name__ == '__main__':
    app.run(debug=False, host-'0.0.0.0')
