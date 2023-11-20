
def get_mass(voltage):
    # regression equation: f(X) = a*x^b+c
    if voltage == 0.0:
        return 0.0
    a = -0.856600000000000
    b = -0.893800000000000
    c = 3.135400000000000
    mass = pow((voltage - c) / a, 1/b)
    return mass


if __name__ == "__main__":
    print(get_mass(1.66))
