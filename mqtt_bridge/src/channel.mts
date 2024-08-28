export class Channel<T> {
  public split(): [Tx<T>, Rx<T>] {
    const rxChannel = new RxChannel<T>();
    const txChannel = new TxChannel(rxChannel);
    return [txChannel, rxChannel];
  }
}

export interface Tx<T> {
  queue(val: T): void;
}

export interface Rx<T> {
  hasEntries(): boolean;

  shift(): T | undefined;

  size(): number;
}

export class TxChannel<T> implements Tx<T> {
  constructor(private readonly rxChannel: RxChannel<T>) {}

  public queue(val: T) {
    this.rxChannel.pass(val);
  }
}

export class RxChannel<T> implements Rx<T> {
  private readonly queue: T[] = [];

  pass(val: T) {
    this.queue.push(val);
  }

  public hasEntries(): boolean {
    return this.queue.length > 0;
  }

  public shift(): T | undefined {
    return this.queue.shift();
  }
  
  public size(): number {
    return this.queue.length;
  }
}
