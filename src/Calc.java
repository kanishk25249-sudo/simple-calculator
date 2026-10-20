import java.util.Scanner;
import java.util.ArrayList;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;

public class Calc {

    // 1. Declare the native method
    static int sub(int a, int b) {
        return a - b;
    }

    static native int calculate(int a, char op, int b);

    // 2. Load the native library
    static {
        System.loadLibrary("calc");
    }

    // Does ONE operation like 7 + 5. C does the work, Java double checks it.
    static int apply_operation(int left_number, char operator_char, int right_number) {

        // "long" is a bigger box for numbers, so this check can't overflow
        long expected_answer;

        if (operator_char == '+') {
            expected_answer = (long) left_number + right_number;
        }
        else if (operator_char == '-') {
            expected_answer = (long) left_number - right_number;
        }
        else if (operator_char == '*') {
            expected_answer = (long) left_number * right_number;
        }
        else {
            if (right_number == 0) {
                throw new RuntimeException("Division by zero");
            }
            expected_answer = (long) left_number / right_number;
        }

        // if the true answer doesn't fit in a normal int, stop
        if (expected_answer > Integer.MAX_VALUE || expected_answer < Integer.MIN_VALUE) {
            throw new RuntimeException("Overflow: answer doesn't fit in 32 bits");
        }

        int answer_from_c = calculate(left_number, operator_char, right_number);

        if (answer_from_c != expected_answer) {
            throw new RuntimeException("Internal error: C gave " + answer_from_c + " but the answer is " + expected_answer);
        }

        return answer_from_c;
    }

    // Writes the answer's lowest 8 bits as binary text, like 00001100, to result.txt
    static void save_result_bits(int result) {
        String bits = String.format("%8s", Integer.toBinaryString(result & 0xFF)).replace(' ', '0');
        try {
            Files.writeString(Path.of("result.txt"), bits);
        }
        catch (IOException e) {
            System.out.println("(could not write result.txt)");
        }
    }

    static void evaluate(String text) {
        if (text.length() == 0) {
            throw new RuntimeException("Type a sum like 10+5*2 cuhhhh.");
        }

        ArrayList<Integer> numbers = new ArrayList<Integer>();
        ArrayList<Character> operators = new ArrayList<Character>();

        int position = 0;

        while (position < text.length()) {

            // 1. read the minus signs in front of the number (each minus flips the sign)
            boolean is_negative = false;
            while (position < text.length() && text.charAt(position) == '-') {
                is_negative = !is_negative;
                position = position + 1;
            }

            // 2. read the digits of the number
            int digits_start = position;
            while (position < text.length() && Character.isDigit(text.charAt(position))) {
                position = position + 1;
            }

            if (position == digits_start) {
                throw new RuntimeException("Expected a number but found something else (bro yk numbers ?)");
            }

            String digits = text.substring(digits_start, position);
            if (is_negative) {
                digits = "-" + digits;
            }

            try {
                numbers.add(Integer.parseInt(digits));
            }
            catch (NumberFormatException e) {
                throw new RuntimeException("Number too large for 32 bits: " + digits);
            }

            // 3. read the operator after the number (if there is one)
            if (position < text.length()) {
                char operator_char = text.charAt(position);

                if (operator_char != '+' && operator_char != '-' && operator_char != '*' && operator_char != '/') {
                    throw new RuntimeException("Unexpected character '" + operator_char + "'");
                }

                operators.add(operator_char);
                position = position + 1;
            }
        }

        // 3 numbers need exactly 2 operators between them
        if (operators.size() != numbers.size() - 1) {
            throw new RuntimeException("The sum ends with an operator, it needs a number after it (whatchu typing cuhhh)");
        }

        // PASS 1: do all the * and / first (left to right)
        int index = 0;
        while (index < operators.size()) {
            char current_operator = operators.get(index);

            if (current_operator == '*' || current_operator == '/') {
                int answer = apply_operation(numbers.get(index), current_operator, numbers.get(index + 1));

                // replace "left number, operator, right number" with just the answer
                numbers.set(index, answer);
                numbers.remove(index + 1);
                operators.remove(index);

                // we do NOT move index forward, because the next operator slid into this spot
            }
            else {
                index = index + 1;
            }
        }

        // PASS 2: only + and - are left, do them left to right
        int result = numbers.get(0);
        for (int i = 0; i < operators.size(); i = i + 1) {
            result = apply_operation(result, operators.get(i), numbers.get(i + 1));
        }

        System.out.println(result);
        save_result_bits(result);
    }

    // 3. Entry point
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);

        while (true) {
            System.out.print("calc> ");
            String line = in.nextLine().replace(" ", "");

            if (line.equals("quit")) {
                break;
            }

            try {
                evaluate(line);
            }

            catch (NumberFormatException e) {
                System.out.println("That doesn't look like a valid sum.");
            }
            catch (StringIndexOutOfBoundsException e) {
                System.out.println("Type a sum like 10+5-3.");
            }
            catch (RuntimeException e) {
                System.out.println(e.getMessage());
            }
        }
    }
}