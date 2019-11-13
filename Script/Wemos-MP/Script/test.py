import machine
 
interruptCounter = 0
totalInterruptsCounter = 0
 
def callback(pin):
  global interruptCounter
  interruptCounter = interruptCounter+1
 
p5 = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
 
p5.irq(trigger=machine.Pin.IRQ_FALLING, handler=callback)
 
while True:
 
  if interruptCounter>0:
 
    state = machine.disable_irq()
    interruptCounter = interruptCounter-1
    machine.enable_irq(state)
 
    totalInterruptsCounter = totalInterruptsCounter+1
    print("Interrupt has occurred: " + str(totalInterruptsCounter))