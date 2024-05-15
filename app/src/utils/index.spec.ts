import { beforeEach, describe, expect, it, vitest } from "vitest";
import { useSleep } from ".";
import { ref, type Ref } from "vue";

describe("Utils", () => {
  describe("useSleep", () => {
    let isRunning: Ref<boolean>;

    beforeEach(() => {
      isRunning = ref(true);
      vitest.useFakeTimers();
      vitest.spyOn(global, "setTimeout");
      vitest.spyOn(global, "clearTimeout");
    });

    const sleep = (ms?: number) => useSleep(isRunning)(ms);

    describe("is running", () => {
      it("sets a timer with duration", () => {
        sleep(1000);
        expect(setTimeout).toHaveBeenCalledOnce();
        expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 1000);
      });

      it("sets a timer without duration", () => {
        sleep();
        expect(setTimeout).toHaveBeenCalledOnce();
        expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), undefined);
      });

      it("resolves the promise", async () => {
        const wait = sleep();
        vitest.runAllTimers();

        await expect(wait).resolves.toBeUndefined();
      });
    });

    describe("is not running", () => {
      it("rejects immediately", async () => {
        isRunning.value = false;
        const wait = sleep(1000);

        await expect(wait).rejects.toBeUndefined();
      });
    });

    describe("cancelling the sleep timer", () => {
      it("cancels the timer", async () => {
        vitest.mocked(global.clearTimeout).mockClear();
        const wait = sleep(1000);
        isRunning.value = false;

        try {
          await wait;
        } catch {
          //
        }

        expect(global.clearTimeout).toHaveBeenCalledOnce();
      });

      it("rejects the promise", async () => {
        const wait = sleep(1000);
        isRunning.value = false;

        await expect(wait).rejects.toBe("aborted");
      });
    });
  });
});
