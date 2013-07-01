import boto.ec2
from fabric.colors import green as _green, yellow as _yellow
from config import *
import time
from mako.template import Template

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'venv', 'aws.cfg')

input_var = input("Enter config file name (in quotes): ")
#f = file(input_var)
f = Template(filename=input_var).render()
cfg = Config(f)
print(_green("Loading ec2 settings")) 


conn = boto.ec2.connect_to_region(cfg['region'], 
  aws_access_key_id=cfg['access_key'],
  aws_secret_access_key=cfg['secret_key'])

def launchInstance():

  user_data = Template(filename=cfg['bootstrap_script']).render(hostname=cfg['hostname'],salt_master_fqdn=cfg['salt_master_fqdn'][0])

  #boot disk
  sda1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
  sda1.size = cfg['boot_disk']['size'] # size in Gigabytes
  if cfg['boot_disk']['volume_type'] == 'io1':
    sda1.volume_type = cfg['boot_disk']['volume_type']
    sda1.iops = cfg['boot_disk']['iops']
  sda1.delete_on_termination = cfg['boot_disk']['delete_on_termination']
  bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
  bdm['/dev/sda1'] = sda1

  #ephemeral disks
  if cfg['ephemeral_disks'] == True:
    sdc1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
    sdd1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
    sde1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
    sdf1 = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
    sdc1.ephemeral_name = 'ephemeral0'
    sdd1.ephemeral_name = 'ephemeral1'
    sde1.ephemeral_name = 'ephemeral2'
    sdf1.ephemeral_name = 'ephemeral3'
    bdm['/dev/sdc1'] = sdc1
    bdm['/dev/sdd1'] = sdd1
    bdm['/dev/sde1'] = sde1
    bdm['/dev/sdf1'] = sdf1


  if cfg['instance_type'] == 'ec2':
    reservation = conn.run_instances(image_id=cfg['ami_id'],
                                     key_name=cfg['key_name'],
                                     instance_type=cfg['instance_size'],
                                     security_groups=cfg['ec2_security_groups'],
                                     ebs_optimized=cfg['ebs_optimized'],
                                     placement=cfg['placement_az'],
                                     user_data=user_data,
                                     block_device_map = bdm
                                     )
  elif cfg['instance_type'] == 'vpc':
    reservation = conn.run_instances(image_id=cfg['ami_id'],
                                     key_name=cfg['key_name'],
                                     instance_type=cfg['instance_size'],
                                     security_group_ids=cfg['vpc_security_group_ids'],
                                     ebs_optimized=cfg['ebs_optimized'],
                                     subnet_id = cfg['vpc_subnet_id'],
                                     placement=cfg['placement_az'],
                                     user_data=user_data,
                                     block_device_map = bdm
                                     )


  instance = reservation.instances[0]

  # Check up on its status every so often
  status = instance.update()
  while status == 'pending':
      time.sleep(2)
      print 'still loading instance...'
      status = instance.update()

  if status == 'running':
      for i in cfg['tags']:
        instance.add_tag(i, cfg['tags'][i])
        print('Added tag: ' + i + ' ' + cfg['tags'])
      print('New instance "' + instance.id + '" accessible at ' + instance.private_dns_name)
  else:
      print('Instance status: ' + status)
      return

  if cfg['data_disk_options']['enabled'] == True:
    #attach EBS Drive
    attachEBS(instance)

def attachEBS(instance):
  '''Attach the default-sized EBS volume to that instance''' 
  # Create a volume in the same availability zone as the instance
  vol = conn.create_volume(cfg['data_disk_size'], instance.placement)
  # Attach it as /dev/sdh
  vol_status = vol.attach(instance.id, '/dev/sdb1')  
  print('created volume:' + vol_status)   
