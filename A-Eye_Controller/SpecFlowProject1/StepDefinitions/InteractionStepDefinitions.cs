using System;
using TechTalk.SpecFlow;

namespace SpecFlowProject1.StepDefinitions
{
    [Binding]
    public class InteractionStepDefinitions
    {
        private readonly Thread _thread;

        public InteractionStepDefinitions()
        {
            _thread = new Thread(AEye.Program.Main);
            _thread.Start();
        }


        [Given(@"the app is connected")]
        public void GivenTheAppIsConnected()
        {
            AEye.Program.controller.Ip_btn_Click(new object(), new EventArgs());
            Thread.Sleep(2000);
        }

        [Given(@"the selected mode is ""([^""]*)""")]
        public void GivenTheSelectedModeIs(string p0)
        {
            if (p0.Equals("mode auto"))
            {
                AEye.Program.controller.setMode(0);
            }
            else if (p0.Equals("mode manual"))
            {
                AEye.Program.controller.setMode(1);
            }
            else if (p0.Equals("mode video"))
            {
                AEye.Program.controller.setMode(2);
            }
            else
            {
                throw new PendingStepException();
            }
        }

        private bool logContainStr(string subStr)
        {
            string ack = AEye.Program.log.Split('\n').Last().ToLower();
            return ack.Contains(subStr.ToLower());
        }


        [Then(@"the system is in ""([^""]*)""")]
        public void ThenTheSystemIsIn(string p0)
        {
            if (p0.Equals("mode auto"))
            {
                logContainStr("Process IA running").Should().BeTrue();
            }
            else if (p0.Equals("mode manual"))
            {
                logContainStr("Mode capture manuelle").Should().BeTrue();
            }
            else if (p0.Equals("mode video"))
            {
                logContainStr("Mode video").Should().BeTrue();
            }
            else
            {
                throw new PendingStepException();
            }
        }

        [Given(@"the current mode is ""([^""]*)""")]
        public void GivenTheCurrentModeIs(string p0)
        {
            if (p0.Equals("mode manual"))
            {
                GivenTheSelectedModeIs(p0);
                //WhenIClickOn("set config");
                Thread.Sleep(1000);
            }
            else
            {
                throw new PendingStepException();
            }
        }

        [Then(@"I must receive a picture")]
        public void ThenIMustReceiveAPicture()
        {
            logContainStr("Get New Image").Should().BeTrue();
        }
    }
}