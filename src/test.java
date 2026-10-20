public class test {
    public static void main(String[] args) {
        int failures = 0;

        int[] nums = {0, -1, 7, 3000000, 2147483647};

        for (int a : nums) {
            for (int b : nums) {

                int gotAdd = Calc.calculate(a, '+', b);
                int wantAdd = a + b;               // Java's own a plus b

                if (gotAdd != wantAdd) {
                    System.out.println("FAIL: " + a + " + " + b + " gave " + gotAdd);
                    failures++;
                }

                int gotSub = Calc.calculate(a, '-', b);
                int wantSub = a - b;               // Java's own a minus b

                if (gotSub != wantSub) {
                    System.out.println("FAIL: " + a + " + " + b + " gave " + gotAdd);
                    failures++;
                }
            }
        }

        System.out.println(failures + " failures");
    }
}
