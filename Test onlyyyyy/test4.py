def main():
    """
    Main function to orchestrate the payroll calculation.
    """
    hours_worked, hourly_rate = get_input()
    gross_pay = calc_gross_pay(hours_worked, hourly_rate)
    overtime_pay = calc_overtime(hours_worked, hourly_rate)
    total_gross_pay = gross_pay + overtime_pay  # Assuming overtime is added to gross
    taxes, benefits = calc_withholdings(total_gross_pay)
    net_pay = calc_net_pay(total_gross_pay, taxes, benefits)

    print(f"\n--- Payroll Summary ---")
    print(f"Hours Worked: {hours_worked}")
    print(f"Hourly Rate: ${hourly_rate:.2f}")
    print(f"Regular Gross Pay: ${gross_pay:.2f}")
    print(f"Overtime Pay: ${overtime_pay:.2f}")
    print(f"Total Gross Pay: ${total_gross_pay:.2f}")
    print(f"Taxes Withheld: ${taxes:.2f}")
    print(f"Benefits Deducted: ${benefits:.2f}")
    print(f"Net Pay: ${net_pay:.2f}")

def get_input():
    """
    Gets the hours worked and hourly rate from the user.
    """
    hours = get_hours_worked()
    rate = get_hourly_rate()
    return hours, rate

def get_hours_worked():
    """
    Prompts the user for hours worked and validates the input.
    """
    while True:
        try:
            hours = float(input("Enter hours worked: "))
            if hours >= 0:
                return hours
            else:
                print("Hours worked cannot be negative. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number for hours worked.")

def get_hourly_rate():
    """
    Prompts the user for hourly rate and validates the input.
    """
    while True:
        try:
            rate = float(input("Enter hourly rate: $"))
            if rate >= 0:
                return rate
            else:
                print("Hourly rate cannot be negative. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number for hourly rate.")

def calc_gross_pay(hours, rate):
    """
    Calculates the regular gross pay (without overtime).
    Assumes standard 40-hour work week for regular pay.
    """
    standard_hours = min(hours, 40)
    return standard_hours * rate

def calc_overtime(hours, rate):
    """
    Calculates overtime pay. Assumes overtime is hours > 40 at 1.5 times the rate.
    """
    if hours > 40:
        overtime_hours = hours - 40
        return overtime_hours * (rate * 1.5)
    return 0

def calc_withholdings(gross_pay):
    """
    Calculates total withholdings, including taxes and benefits.
    """
    taxes = calc_taxes(gross_pay)
    benefits = calc_benefits(gross_pay)
    return taxes, benefits

def calc_taxes(gross_pay):
    """
    Calculates taxes based on gross pay. (Placeholder for actual tax logic)
    For demonstration, let's assume a flat 15% tax rate.
    """
    tax_rate = 0.15
    return gross_pay * tax_rate

def calc_benefits(gross_pay):
    """
    Calculates benefit deductions. (Placeholder for actual benefit logic)
    For demonstration, let's assume a fixed benefit deduction or a percentage.
    Let's use a flat 5% of gross pay for benefits.
    """
    benefit_rate = 0.05
    return gross_pay * benefit_rate

def calc_net_pay(total_gross_pay, taxes, benefits):
    """
    Calculates the net pay after deducting taxes and benefits.
    """
    return total_gross_pay - (taxes + benefits)

if __name__ == "__main__":
    main()